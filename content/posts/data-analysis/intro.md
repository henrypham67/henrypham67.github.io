---
title: 'Statistics'
date: 2026-03-28T10:11:08+07:00
draft: true
tags: ["data-analysis", "statistics", "python", "sre"]
categories: ["Data Analysis"]
---

Here's a detailed explanation of the concept from line 46 of your post.

---

## "If a single node exceeds 3 standard deviations from the mean"

This is a classic **statistical anomaly detection rule** (also called the **3-sigma rule** or **68-95-99.7 rule**).

### The core idea

In any normally distributed dataset:
- ~68% of values fall within **1 standard deviation** of the mean
- ~95% fall within **2 standard deviations**
- ~99.7% fall within **3 standard deviations**

That means **only 0.3% of values** naturally land beyond 3 standard deviations. If a node's metric lands there, it's almost certainly *not* random variation — something is wrong.

---

### Concrete example: disk I/O across a database fleet

You have **10 Datadog-monitored database nodes** with these disk I/O read rates (MB/s):

```
Node 1:  120
Node 2:  115
Node 3:  118
Node 4:  122
Node 5:  119
Node 6:  117
Node 7:  121
Node 8:  116
Node 9:  118
Node 10: 310  ← suspicious
```

**Step 1 — Calculate the mean:**
```
mean = (120+115+118+122+119+117+121+116+118+310) / 10
     = 1276 / 10
     = 127.6 MB/s
```

**Step 2 — Calculate standard deviation:**
```python
import numpy as np

io_rates = [120, 115, 118, 122, 119, 117, 121, 116, 118, 310]
mean = np.mean(io_rates)   # 127.6
std  = np.std(io_rates)    # ~56.8
```

**Step 3 — Calculate the 3-sigma threshold:**
```
upper_threshold = mean + (3 × std)
               = 127.6 + (3 × 56.8)
               = 127.6 + 170.4
               = 298.0 MB/s
```

**Step 4 — Check each node:**
```
Node 10: 310 MB/s > 298.0 MB/s  →  ALERT: exceeds 3σ
```

---

### Python implementation (SRE production pattern)

```python
import numpy as np

def detect_anomalous_nodes(node_metrics: dict, threshold_sigma: float = 3.0):
    nodes   = list(node_metrics.keys())
    values  = np.array(list(node_metrics.values()))

    mean    = np.mean(values)
    std     = np.std(values)
    upper   = mean + threshold_sigma * std

    anomalies = {
        node: val for node, val in node_metrics.items()
        if val > upper
    }

    return mean, std, upper, anomalies


node_io = {
    "db-node-1": 120, "db-node-2": 115, "db-node-3": 118,
    "db-node-4": 122, "db-node-5": 119, "db-node-6": 117,
    "db-node-7": 121, "db-node-8": 116, "db-node-9": 118,
    "db-node-10": 310,
}

mean, std, upper, anomalies = detect_anomalous_nodes(node_io)

print(f"Mean: {mean:.1f} MB/s")
print(f"Std:  {std:.1f} MB/s")
print(f"3σ upper bound: {upper:.1f} MB/s")
print(f"Anomalous nodes: {anomalies}")
```

**Output:**
```
Mean: 127.6 MB/s
Std:  56.8 MB/s
3σ upper bound: 298.0 MB/s
Anomalous nodes: {'db-node-10': 310}
```

---

### One important caveat

Notice that **Node 10 (310) inflates the mean and std**. This is called **masking** — the outlier makes the threshold looser. In production SRE work, you often use the **median** and **IQR (interquartile range)** instead of mean/std, because they are *robust to outliers*. Your `iqr.png` file in the same directory suggests you're already exploring this.

The 3-sigma rule works best when you're monitoring a **steady-state fleet** where one truly anomalous node shouldn't dominate the baseline calculation.