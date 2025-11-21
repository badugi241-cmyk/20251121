"""Binomial option pricing model implementation.

Provides utilities to price European and American call/put options using
Cox-Ross-Rubinstein binomial trees.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

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


__all__ = ["OptionSpec", "price_option"]
