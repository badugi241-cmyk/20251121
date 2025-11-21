"""Binomial option pricing model implementation.

Provides utilities to price European and American call/put options using
Cox-Ross-Rubinstein binomial trees.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Literal, Sequence

OptionType = Literal["call", "put"]


@dataclass
class OptionSpec:
    """Describes the option to price."""

    spot: float
    strike: float
    rate: float
    volatility: float
    maturity: float
    steps: int
    option_type: OptionType = "call"
    american: bool = False

    def validate(self) -> None:
        if self.steps <= 0:
            raise ValueError("steps must be positive")
        if self.spot <= 0 or self.strike <= 0:
            raise ValueError("spot and strike must be positive")
        if self.volatility <= 0:
            raise ValueError("volatility must be positive")
        if self.maturity <= 0:
            raise ValueError("maturity must be positive")
        if self.option_type not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put'")


def _crr_parameters(spec: OptionSpec) -> tuple[float, float, float, float]:
    dt = spec.maturity / spec.steps
    up = math.exp(spec.volatility * math.sqrt(dt))
    down = 1 / up
    discount = math.exp(-spec.rate * dt)
    prob = (math.exp(spec.rate * dt) - down) / (up - down)
    if not 0 < prob < 1:
        raise ValueError("risk-neutral probability out of bounds; adjust parameters")
    return dt, up, down, prob


def _payoff(price: float, strike: float, option_type: OptionType) -> float:
    if option_type == "call":
        return max(price - strike, 0.0)
    return max(strike - price, 0.0)


def monte_carlo_price(
    *,
    spot: float,
    rate: float,
    volatility: float,
    maturity: float,
    steps: int,
    paths: int,
    payoff_fn: Callable[[Sequence[float]], float],
    seed: int | None = None,
) -> float:
    """Price an option via Monte Carlo simulation with a custom payoff.

    The payoff function receives the full simulated price path (including the
    initial spot) so path-dependent options can be priced without additional
    scaffolding.

    Args:
        spot: Current asset price (> 0).
        rate: Risk-free rate.
        volatility: Asset volatility (>= 0).
        maturity: Time to maturity in years (> 0).
        steps: Number of time steps per path (> 0).
        paths: Number of simulated paths (> 0).
        payoff_fn: Callable that accepts a price path and returns its payoff.
        seed: Optional random seed for reproducibility.

    Returns:
        Present value estimated from the simulated payoffs.
    """

    if spot <= 0:
        raise ValueError("spot must be positive")
    if maturity <= 0:
        raise ValueError("maturity must be positive")
    if steps <= 0:
        raise ValueError("steps must be positive")
    if paths <= 0:
        raise ValueError("paths must be positive")
    if volatility < 0:
        raise ValueError("volatility cannot be negative")

    rnd = random.Random(seed)
    dt = maturity / steps
    drift = (rate - 0.5 * volatility * volatility) * dt
    diffusion_scale = volatility * math.sqrt(dt)
    discount = math.exp(-rate * maturity)

    payoff_sum = 0.0
    for _ in range(paths):
        price = spot
        path: list[float] = [price]
        for _ in range(steps):
            shock = rnd.gauss(0.0, 1.0)
            price *= math.exp(drift + diffusion_scale * shock)
            path.append(price)
        payoff_sum += payoff_fn(path)

    average_payoff = payoff_sum / paths
    return discount * average_payoff


def price_option(spec: OptionSpec) -> float:
    """Price an option using a Cox-Ross-Rubinstein binomial tree.

    Args:
        spec: Option specification.

    Returns:
        Present value of the option.
    """

    spec.validate()
    dt, up, down, prob = _crr_parameters(spec)

    # Terminal payoffs
    prices = [spec.spot * (up**j) * (down ** (spec.steps - j)) for j in range(spec.steps + 1)]
    payoffs = [_payoff(price, spec.strike, spec.option_type) for price in prices]
    discount = math.exp(-spec.rate * dt)

    # Backward induction
    for step in range(spec.steps, 0, -1):
        payoffs = [discount * (prob * payoffs[i + 1] + (1 - prob) * payoffs[i]) for i in range(step)]

        if spec.american:
            current_prices = [spec.spot * (up**i) * (down ** (step - 1 - i)) for i in range(step)]
            early_exercise = [_payoff(price, spec.strike, spec.option_type) for price in current_prices]
            payoffs = [max(continuation, exercise) for continuation, exercise in zip(payoffs, early_exercise)]

    return payoffs[0]


__all__ = ["OptionSpec", "price_option", "monte_carlo_price"]
