"""Simple Flask app to price options via Monte Carlo simulation.

The service exposes both a web form and a JSON API to compute option
prices using the existing ``monte_carlo_price`` helper. It supports a
plain European payoff (call/put on the terminal price) and an
arithmetic-average Asian payoff (call/put on the average price of the
path).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from flask import Flask, jsonify, render_template_string, request

from binomial_model import monte_carlo_price

OptionType = Literal["call", "put"]
PayoffStyle = Literal["european", "asian_average"]


@dataclass
class SimulationInput:
    """Input payload expected by the service."""

    spot: float
    strike: float
    rate: float
    volatility: float
    maturity: float
    steps: int
    paths: int
    option_type: OptionType
    payoff_style: PayoffStyle

    @classmethod
    def from_request(cls, payload: dict[str, str | float]) -> "SimulationInput":
        try:
            spot = float(payload["spot"])
            strike = float(payload["strike"])
            rate = float(payload["rate"])
            volatility = float(payload["volatility"])
            maturity = float(payload["maturity"])
            steps = int(payload["steps"])
            paths = int(payload["paths"])
            option_type = str(payload.get("option_type", "call"))
            payoff_style = str(payload.get("payoff_style", "european"))
        except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - simple guard
            raise ValueError("Missing or invalid parameters") from exc

        if option_type not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put'")
        if payoff_style not in ("european", "asian_average"):
            raise ValueError("Invalid payoff_style")

        return cls(
            spot=spot,
            strike=strike,
            rate=rate,
            volatility=volatility,
            maturity=maturity,
            steps=steps,
            paths=paths,
            option_type=option_type,  # type: ignore[arg-type]
            payoff_style=payoff_style,  # type: ignore[arg-type]
        )

    def payoff(self) -> Callable[[list[float]], float]:
        if self.payoff_style == "asian_average":
            return self._asian_payoff
        return self._european_payoff

    def _european_payoff(self, path: list[float]) -> float:
        terminal = path[-1]
        if self.option_type == "call":
            return max(terminal - self.strike, 0.0)
        return max(self.strike - terminal, 0.0)

    def _asian_payoff(self, path: list[float]) -> float:
        average_price = sum(path) / len(path)
        if self.option_type == "call":
            return max(average_price - self.strike, 0.0)
        return max(self.strike - average_price, 0.0)


def price_option(input_data: SimulationInput) -> float:
    return monte_carlo_price(
        spot=input_data.spot,
        rate=input_data.rate,
        volatility=input_data.volatility,
        maturity=input_data.maturity,
        steps=input_data.steps,
        paths=input_data.paths,
        payoff_fn=input_data.payoff(),
    )


def build_app() -> Flask:
    app = Flask(__name__)

    @app.post("/api/price")
    def api_price():
        try:
            payload = request.get_json(force=True, silent=False)
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object")
            sim_input = SimulationInput.from_request(payload)
            price = price_option(sim_input)
            return jsonify({"price": price})
        except Exception as exc:  # pragma: no cover - thin facade
            return jsonify({"error": str(exc)}), 400

    @app.route("/", methods=["GET", "POST"])
    def form():
        price = None
        error = None
        form_data = {
            "spot": "100",
            "strike": "100",
            "rate": "0.05",
            "volatility": "0.2",
            "maturity": "1",
            "steps": "64",
            "paths": "5000",
            "option_type": "call",
            "payoff_style": "european",
        }

        if request.method == "POST":
            form_data.update(request.form)
            try:
                sim_input = SimulationInput.from_request(form_data)
                price = price_option(sim_input)
            except Exception as exc:  # pragma: no cover - thin facade
                error = str(exc)

        return render_template_string(
            _HTML_TEMPLATE,
            price=price,
            error=error,
            form_data=form_data,
        )

    return app


_HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Monte Carlo Option Calculator</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem auto; max-width: 720px; }
      h1 { color: #1e4c7a; }
      form { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem 1rem; }
      label { font-weight: bold; }
      input, select { padding: 0.5rem; }
      .full-width { grid-column: 1 / -1; }
      .result { background: #eef6ff; padding: 0.75rem 1rem; margin-top: 1rem; border-radius: 6px; }
      .error { background: #ffeaea; padding: 0.75rem 1rem; margin-top: 1rem; border-radius: 6px; color: #8a1c1c; }
      button { padding: 0.6rem 1rem; background: #1e4c7a; color: white; border: none; border-radius: 4px; cursor: pointer; }
      button:hover { background: #163c5f; }
    </style>
  </head>
  <body>
    <h1>Monte Carlo Option Calculator</h1>
    <p>Simulate European or arithmetic-average Asian options using a simple Monte Carlo engine.</p>
    <form method="post">
      <div>
        <label for="spot">Spot</label>
        <input type="number" step="any" id="spot" name="spot" required value="{{ form_data.spot }}">
      </div>
      <div>
        <label for="strike">Strike</label>
        <input type="number" step="any" id="strike" name="strike" required value="{{ form_data.strike }}">
      </div>
      <div>
        <label for="rate">Risk-free rate</label>
        <input type="number" step="any" id="rate" name="rate" required value="{{ form_data.rate }}">
      </div>
      <div>
        <label for="volatility">Volatility</label>
        <input type="number" step="any" id="volatility" name="volatility" required value="{{ form_data.volatility }}">
      </div>
      <div>
        <label for="maturity">Maturity (years)</label>
        <input type="number" step="any" id="maturity" name="maturity" required value="{{ form_data.maturity }}">
      </div>
      <div>
        <label for="steps">Steps</label>
        <input type="number" step="1" min="1" id="steps" name="steps" required value="{{ form_data.steps }}">
      </div>
      <div>
        <label for="paths">Paths</label>
        <input type="number" step="1" min="1" id="paths" name="paths" required value="{{ form_data.paths }}">
      </div>
      <div>
        <label for="option_type">Option type</label>
        <select id="option_type" name="option_type">
          <option value="call" {% if form_data.option_type == 'call' %}selected{% endif %}>Call</option>
          <option value="put" {% if form_data.option_type == 'put' %}selected{% endif %}>Put</option>
        </select>
      </div>
      <div>
        <label for="payoff_style">Payoff</label>
        <select id="payoff_style" name="payoff_style">
          <option value="european" {% if form_data.payoff_style == 'european' %}selected{% endif %}>European (terminal)</option>
          <option value="asian_average" {% if form_data.payoff_style == 'asian_average' %}selected{% endif %}>Asian arithmetic average</option>
        </select>
      </div>
      <div class="full-width">
        <button type="submit">Run simulation</button>
      </div>
    </form>

    {% if price is not none %}
      <div class="result">Estimated price: <strong>{{ '%.4f' % price }}</strong></div>
    {% endif %}
    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}
    <div class="result">
      <p><strong>API usage:</strong> POST <code>/api/price</code> with JSON:</p>
      <pre>{
  "spot": 100,
  "strike": 100,
  "rate": 0.05,
  "volatility": 0.2,
  "maturity": 1,
  "steps": 64,
  "paths": 5000,
  "option_type": "call",
  "payoff_style": "european"
}</pre>
    </div>
  </body>
</html>
"""


if __name__ == "__main__":
    app = build_app()
    app.run(host="0.0.0.0", port=8000, debug=False)
