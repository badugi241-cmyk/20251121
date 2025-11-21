import math
import unittest

from binomial_model import monte_carlo_price


class MonteCarloPriceTest(unittest.TestCase):
    def test_deterministic_zero_vol_call(self):
        strike = 100
        maturity = 1.0
        rate = 0.05
        price = monte_carlo_price(
            spot=100,
            rate=rate,
            volatility=0.0,
            maturity=maturity,
            steps=5,
            paths=1000,
            payoff_fn=lambda path: max(path[-1] - strike, 0.0),
            seed=7,
        )
        expected_terminal = 100 * math.exp(rate * maturity)
        expected_payoff = max(expected_terminal - strike, 0.0)
        expected_price = expected_payoff * math.exp(-rate * maturity)
        self.assertAlmostEqual(price, expected_price, places=6)

    def test_path_dependent_average_price(self):
        rate = 0.02
        maturity = 0.5
        price = monte_carlo_price(
            spot=50,
            rate=rate,
            volatility=0.0,
            maturity=maturity,
            steps=4,
            paths=500,
            payoff_fn=lambda path: max(sum(path) / len(path) - 50, 0.0),
            seed=123,
        )
        deterministic_path = [50 * math.exp(rate * maturity * i / 4) for i in range(5)]
        expected_average = sum(deterministic_path) / len(deterministic_path)
        expected_price = max(expected_average - 50, 0.0) * math.exp(-rate * maturity)
        self.assertAlmostEqual(price, expected_price, places=6)


if __name__ == "__main__":
    unittest.main()
