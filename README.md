# 20251121

## Monte Carlo CLI

You can price path-dependent or vanilla options with a custom payoff using the
included command-line tool:

```
python -m monte_carlo_cli \
  --spot 100 \
  --rate 0.05 \
  --volatility 0.2 \
  --maturity 1.0 \
  --steps 252 \
  --paths 10000 \
  --payoff ./my_payoff.py \
  --function payoff \
  --seed 123
```

The referenced `my_payoff.py` file must define a function accepting the
simulated price path. For example:

```python
def payoff(path: list[float]) -> float:
    # Asian call on the average price
    average_price = sum(path) / len(path)
    return max(average_price - 100, 0.0)
```
