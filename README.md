# 20251121

Monte Carlo and binomial option pricing utilities with a lightweight web UI.

## Getting started

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the web server:
   ```bash
   python web_app.py
   ```
4. Open http://localhost:8000 to access the form UI.

## Web usage

### Browser form
- Enter the option parameters (spot, strike, risk-free rate, volatility, maturity, steps, paths).
- Choose **Option type** (call/put) and **Payoff**:
  - *European (terminal)* prices based on the final price only.
  - *Asian arithmetic average* prices based on the average price across the path.
- Click **Run simulation** to see the estimated price.

### JSON API
POST to `/api/price` with JSON:
```json
{
  "spot": 100,
  "strike": 100,
  "rate": 0.05,
  "volatility": 0.2,
  "maturity": 1,
  "steps": 64,
  "paths": 5000,
  "option_type": "call",
  "payoff_style": "european"
}
```

Response:
```json
{"price": 10.23}
```
If validation fails, the response includes an `error` message with a 400 status code.

## Tests
Run the existing unit tests:
```bash
python -m pytest
```
