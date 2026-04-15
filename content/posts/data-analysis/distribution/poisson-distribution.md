---
title: 'Poisson distribution'
date: 2026-04-07T17:26:41+07:00
draft: true
tags: ["statistics", "probability", "distributions"]
categories: ["Data Analysis"]
---

The Poisson distribution models how many times a random event happens in a fixed
interval of time or space — when events occur independently and at a known average
rate.

---
2. The Analogy

Think of a coffee shop that averages 3 customers per minute. You can't predict exactly
when each customer walks in — but you can ask: "What's the probability that exactly 5
customers arrive in the next minute?"

That's exactly what the Poisson distribution answers. The "interval" is one minute, the
  "rate" (λ, lambda) is 3, and you're asking about k=5 arrivals.

Where the analogy breaks down: Poisson assumes customers arrive independently — one
customer showing up doesn't make the next more or less likely. If customers come in
groups (families), the model gets less accurate.

---
3. How It Actually Works

The Poisson distribution has one parameter: λ (lambda) — the average number of events
per interval.

The formula:

P(X = k) = (λ^k × e^(-λ)) / k!

Where:
- k = the number of events you want the probability for
- λ = average rate (must be > 0)
- e ≈ 2.718 (Euler's number)

Step by step for our coffee shop (λ=3, k=5):

1. Compute λ^k = 3^5 = 243
2. Compute e^(-λ) = e^(-3) ≈ 0.0498
3. Compute k! = 5! = 120
4. P(X=5) = (243 × 0.0498) / 120 ≈ 0.101 (about 10% chance)

λ (avg rate) ──► Poisson formula ──► P(exactly k events)
      3                                      10%

The distribution looks like a skewed bell curve — peak near λ, tapering off on both
sides.

Great follow-up. Here are the most practical applications, with real examples you'd encounter on the job:

---

## 1. Alerting Threshold Calibration

**Problem:** Your alert fires when requests/sec drops below X. Is that threshold triggering false alarms?

```python
from scipy.stats import poisson

lam = 200  # avg requests/sec (from your metrics)
threshold = 150

# Probability this happens by pure chance (not an outage)
false_alarm_rate = poisson.cdf(k=threshold, mu=lam)
print(f"False alarm probability: {false_alarm_rate:.4%}")
# If this is 5%+, your threshold needs tuning
```

**Rule:** If P(X ≤ threshold) > 1%, expect frequent false pages.

---

## 2. Incident Rate Modeling

You average 2 incidents/week. What's the probability you get hit with 5+ this week?

```python
lam = 2  # avg incidents per week

# P(5 or more incidents this week)
p_bad_week = 1 - poisson.cdf(k=4, mu=lam)
print(f"Probability of 5+ incidents: {p_bad_week:.2%}")  # ~5.3%

# Useful for: on-call scheduling, SLA planning, staffing decisions
```

---

## 3. Capacity Planning / Auto-scaling

If your service gets λ=500 req/sec average, you need to handle the **tail** — not just the average:

```python
lam = 500

# What's the 99.9th percentile request load?
p999 = poisson.ppf(0.999, mu=lam)
print(f"Size for 99.9% coverage: {p999:.0f} req/sec")  # ~537

# Provision for p999, not the mean — that's where Poisson earns its keep
```

This is how you set **HPA (Horizontal Pod Autoscaler)** max replicas rationally rather than guessing.

---

## 4. Anomaly Detection in Logs

Baseline your error rate, then flag statistical outliers:

```python
from scipy.stats import poisson

baseline_errors_per_hour = 10  # measured from last 30 days

def is_anomaly(observed: int, confidence: float = 0.999) -> bool:
    """Flag if observed count is statistically unusual."""
    upper_bound = poisson.ppf(confidence, mu=baseline_errors_per_hour)
    return observed > upper_bound

print(is_anomaly(25))   # True  → page someone
print(is_anomaly(14))   # False → normal variance
```

This is essentially what **Datadog anomaly detection** and **CloudWatch anomaly alarms** do under the hood.

---

## 5. Deployment Failure Risk

If your deploys fail at rate λ=0.5/week, what's the probability of zero failures in a 4-week sprint?

```python
lam_per_sprint = 0.5 * 4  # scale λ to your interval

p_zero_failures = poisson.pmf(k=0, mu=lam_per_sprint)
print(f"Clean sprint probability: {p_zero_failures:.1%}")  # ~13.5%

# Sobering. Use this to justify investing in better CI/CD.
```

---

## The Core DevOps Mental Model

> Any time you're looking at a **rate metric** in your dashboards (errors/min, deploys/day, pages/week) and asking "is this normal or should I be worried?" — you're doing Poisson reasoning.

The practical workflow:

```
1. Establish baseline λ from historical data (last 30 days)
2. Pick a confidence threshold (99%, 99.9%)
3. Compute the upper bound via poisson.ppf()
4. Set your alert at that bound, not at λ + gut_feeling
```

---

## Tools Where This Shows Up Natively

| Tool              | Where Poisson is used                     |
| ----------------- | ----------------------------------------- |
| Datadog           | Anomaly detection, forecast monitors      |
| CloudWatch        | Anomaly detection alarms                  |
| Prometheus        | Used in `predict_linear` + alerting rules |
| PagerDuty         | Alert noise analysis                      |
| Chaos Engineering | Failure injection rate modeling           |

---

Want me to walk through building a concrete alerting script that auto-tunes thresholds from your Prometheus metrics using this approach?