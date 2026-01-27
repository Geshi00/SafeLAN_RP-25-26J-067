# Keystroke Authentication Results Summary

## 📊 Dataset Overview
- **Genuine samples**: 40 (14 features each)
- **Synthetic impostor samples**: 100 (generated via noise + permutation)
- **Total dataset**: 140 samples
- **Train/Test split**: 70/30 (98 train, 42 test)

---

## 🏆 Model Performance Rankings

### Top 3 Models (by F1-Score)

| Rank | Model | F1-Score | Accuracy | FAR | FRR | EER |
|------|-------|----------|----------|-----|-----|-----|
| 🥇 1st | **OneClassSVM** | 1.0000 | 100.0% | 0.0% | 0.0% | 0.0% |
| 🥈 2nd | **Isolation Forest** | 0.9565 | 97.6% | 0.0% | 8.3% | 4.2% |
| 🥉 3rd | **LOF** | 0.9565 | 97.6% | 0.0% | 8.3% | 4.2% |
| 🥉 3rd | **Autoencoder** | 0.9565 | 97.6% | 0.0% | 8.3% | 4.2% |

### All Models Performance

| Model | Accuracy | Precision | Recall | F1-Score | FAR | FRR | EER | TP | TN | FP | FN |
|-------|----------|-----------|--------|----------|-----|-----|-----|----|----|----|----|
| OneClassSVM | 100.0% | 100.0% | 100.0% | 1.0000 | 0.0% | 0.0% | 0.0% | 12 | 30 | 0 | 0 |
| IsolationForest | 97.6% | 100.0% | 91.7% | 0.9565 | 0.0% | 8.3% | 4.2% | 11 | 30 | 0 | 1 |
| LOF | 97.6% | 100.0% | 91.7% | 0.9565 | 0.0% | 8.3% | 4.2% | 11 | 30 | 0 | 1 |
| Autoencoder | 97.6% | 100.0% | 91.7% | 0.9565 | 0.0% | 8.3% | 4.2% | 11 | 30 | 0 | 1 |
| GMM | 88.1% | 100.0% | 58.3% | 0.7368 | 0.0% | 41.7% | 20.8% | 7 | 30 | 0 | 5 |
| EllipticEnvelope | 83.3% | 64.7% | 91.7% | 0.7586 | 20.0% | 8.3% | 14.2% | 11 | 24 | 6 | 1 |

---

## 🎯 Key Insights

### ✅ Excellent Performance
1. **OneClassSVM achieved perfect 100% accuracy** - No errors on test set
2. **Zero False Acceptance Rate (FAR)** across top 4 models - Critical for security
3. **Three models tied at 97.6% accuracy** - Consistent high performance

### ⚠️ Important Observations
1. **Perfect scores may indicate overfitting** - Synthetic impostors might be too easy to detect
2. **Low False Rejection Rate (FRR)** - Good user experience (genuine users rarely rejected)
3. **GMM shows high FRR (41.7%)** - Would frustrate legitimate users

---

## 🔬 Detailed Model Analysis

### 🥇 OneClassSVM (Winner)
**Hyperparameters:**
- Kernel: RBF
- Gamma: 0.01
- Nu: 0.05

**Performance:**
- **Perfect classification**: 12/12 genuine, 30/30 impostors
- **No false positives or negatives**
- **Best for production deployment**

**Pros:**
- Excellent boundary learning
- Robust to outliers
- Fast inference

**Cons:**
- May be overfitting synthetic data
- Needs validation with real impostors

---

### 🥈 Isolation Forest
**Hyperparameters:**
- Contamination: 0.15
- N_estimators: 50
- Max_samples: auto

**Performance:**
- **1 False Negative** (1 genuine user rejected)
- **0 False Positives** (no impostors accepted)
- **8.3% FRR** - Acceptable for most applications

**Pros:**
- Fast training
- Good anomaly detection
- Scalable to large datasets

---

### 🥉 Local Outlier Factor (LOF)
**Hyperparameters:**
- N_neighbors: 10
- Contamination: 0.2

**Performance:**
- **Identical to Isolation Forest** (1 FN, 0 FP)
- **Good density-based detection**

**Pros:**
- Effective for local anomalies
- No assumptions about data distribution

---

### 🏅 Autoencoder
**Performance:**
- **Matched top performers** (97.6% accuracy)
- **Same error pattern** as Isolation Forest

**Pros:**
- Can learn complex patterns
- Adaptable architecture
- Good for high-dimensional data

**Cons:**
- Slower training
- More hyperparameters to tune

---

### ⚠️ Gaussian Mixture Model (GMM)
**Issues:**
- **High FRR (41.7%)** - Rejects too many genuine users
- **5 False Negatives** - Poor genuine user experience
- **Not recommended for production**

**Why it underperformed:**
- Single component may not capture pattern variability
- Keystroke data may not follow Gaussian distribution

---

### ⚠️ Elliptic Envelope
**Issues:**
- **High FAR (20%)** - Accepts 1 in 5 impostors
- **6 False Positives** - Security risk
- **Not recommended for authentication**

**Why it underperformed:**
- Assumes elliptical (Gaussian) distribution
- Keystroke timing is often non-Gaussian

---

## 📈 Biometric Security Metrics

### Equal Error Rate (EER) Analysis
**Industry Benchmark**: EER < 5% is considered excellent

| Model | EER | Rating | Status |
|-------|-----|--------|--------|
| OneClassSVM | 0.0% | ⭐⭐⭐⭐⭐ Exceptional | ✅ Pass |
| Isolation Forest | 4.2% | ⭐⭐⭐⭐ Excellent | ✅ Pass |
| LOF | 4.2% | ⭐⭐⭐⭐ Excellent | ✅ Pass |
| Autoencoder | 4.2% | ⭐⭐⭐⭐ Excellent | ✅ Pass |
| EllipticEnvelope | 14.2% | ⭐⭐ Fair | ⚠️ Review |
| GMM | 20.8% | ⭐ Poor | ❌ Fail |

---

