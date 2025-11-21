"""Command-line interface for Monte Carlo option pricing with custom payoffs."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable, Sequence

from binomial_model import monte_carlo_price

PayoffFn = Callable[[Sequence[float]], float]


def _load_module(module_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("user_payoff", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_payoff(module_path: str, function_name: str = "payoff") -> PayoffFn:
    """Load a payoff function from a Python file.

    The referenced function must accept a sequence of simulated prices and
    return the payoff for that path. This allows users to define arbitrary
    payoffs, including path-dependent ones (e.g., Asian options).
    """

    path = Path(module_path)
    if not path.is_file():
        raise FileNotFoundError(f"Payoff module not found: {module_path}")

    module = _load_module(path)
    try:
        payoff_fn = getattr(module, function_name)
    except AttributeError as exc:  # pragma: no cover - defensive branch
        raise AttributeError(
            f"Function '{function_name}' not found in {module_path}"
        ) from exc

    if not callable(payoff_fn):
        raise TypeError(f"{function_name} in {module_path} is not callable")

    return payoff_fn  # type: ignore[return-value]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Monte Carlo option pricing with a user-provided payoff function. "
            "Provide a Python file containing a payoff(path) function."
        )
    )

    parser.add_argument("--spot", type=float, required=True, help="Current spot price")
    parser.add_argument("--rate", type=float, required=True, help="Risk-free interest rate")
    parser.add_argument("--volatility", type=float, required=True, help="Asset volatility")
    parser.add_argument("--maturity", type=float, required=True, help="Time to maturity in years")
    parser.add_argument("--steps", type=int, required=True, help="Number of time steps per path")
    parser.add_argument("--paths", type=int, required=True, help="Number of simulated paths")
    parser.add_argument(
        "--payoff",
        type=str,
        required=True,
        help="Path to a Python file defining the payoff function",
    )
    parser.add_argument(
        "--function",
        type=str,
        default="payoff",
        help="Name of the payoff function inside the module (default: payoff)",
    )
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payoff_fn = load_payoff(args.payoff, args.function)

        price = monte_carlo_price(
            spot=args.spot,
            rate=args.rate,
            volatility=args.volatility,
            maturity=args.maturity,
            steps=args.steps,
            paths=args.paths,
            payoff_fn=payoff_fn,
            seed=args.seed,
        )
    except Exception as exc:  # pragma: no cover - surfaced via CLI tests
        parser.error(str(exc))

    print(f"{price:.8f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
