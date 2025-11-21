import unittest

from binomial_model import OptionSpec, price_option


class BinomialModelTest(unittest.TestCase):
    def test_european_call(self):
        spec = OptionSpec(
            spot=100,
            strike=100,
            rate=0.05,
            volatility=0.2,
            maturity=1,
            steps=3,
            option_type="call",
            american=False,
        )
        price = price_option(spec)
        self.assertAlmostEqual(price, 11.043871091951113, places=9)

    def test_european_put(self):
        spec = OptionSpec(
            spot=100,
            strike=100,
            rate=0.05,
            volatility=0.2,
            maturity=1,
            steps=3,
            option_type="put",
            american=False,
        )
        price = price_option(spec)
        self.assertAlmostEqual(price, 6.166813542022532, places=9)

    def test_american_put_more_valuable(self):
        euro_put = OptionSpec(
            spot=100,
            strike=100,
            rate=0.05,
            volatility=0.2,
            maturity=1,
            steps=3,
            option_type="put",
            american=False,
        )
        american_put = OptionSpec(
            spot=100,
            strike=100,
            rate=0.05,
            volatility=0.2,
            maturity=1,
            steps=3,
            option_type="put",
            american=True,
        )
        euro_price = price_option(euro_put)
        american_price = price_option(american_put)
        self.assertGreater(american_price, euro_price)
        self.assertAlmostEqual(american_price, 6.499559886616256, places=9)

    def test_invalid_probability(self):
        spec = OptionSpec(
            spot=100,
            strike=100,
            rate=-0.5,
            volatility=0.01,
            maturity=1,
            steps=1,
            option_type="call",
            american=False,
        )
        with self.assertRaises(ValueError):
            price_option(spec)


if __name__ == "__main__":
    unittest.main()
