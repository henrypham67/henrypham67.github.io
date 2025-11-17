---
title: 'Concepts'
date: 2025-08-11T10:15:45+07:00
draft: true
---

## Overfitting vs. underfitting (quickly)

### Overfitting

the model is too complex. It learns real patterns and the noise in the training data. Symptoms: super low training error, noticeably worse test error. Think low bias, high variance.

### Underfitting

the model is too simple. It misses real structure in the data. Symptoms: high training error and high test error. Think high bias, low variance.

A neat way to see it is the error decomposition (for regression):

```text
Test error
≈
Bias
2
+
Variance
+
Noise
.
Test error≈Bias 
2
 +Variance+Noise.
Overfit = big Variance; Underfit = big Bias.

Why larger k in kNN tends to underfit
In k-nearest neighbors, predictions come from the average/majority vote of the k closest points. As you increase 
𝑘
k:

Heavier smoothing
The prediction becomes an average over a wider neighborhood. That smooths away local structure and class boundaries. In the extreme, 
𝑘
=
𝑛
k=n (all points) → every test point gets the global average (regression) or the majority class (classification) — a classic underfit.

Bias ↑, Variance ↓
Small 
𝑘
k (e.g., 
𝑘
=
1
k=1) = very wiggly decision boundary, low bias but high variance (can memorize training set → overfit). Larger 
𝑘
k makes the boundary smoother and more stable, reducing variance but increasing bias. Too large 
𝑘
k pushes you into underfitting.

Local signals get diluted
If a test point sits in a pocket of Class A but you include many distant neighbors (possibly Class B), the majority vote shifts away from the true local label — you’ve averaged away the informative locality.

Practical tips
Tune 
𝑘
k with cross-validation and look for the sweet spot in validation error (U-shaped curve vs. 
𝑘
k).

In classification, distance-weight neighbors (closer ones count more) to reduce the bias you get at larger 
𝑘
k.

In high dimensions, you often need a somewhat larger 
𝑘
k to tame noise, but still guard against making 
𝑘
k so large that you wash out real structure.
```

## Supervised/Unsupervised/Reinforcement Learning
