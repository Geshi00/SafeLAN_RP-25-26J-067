import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.mixture import GaussianMixture
from sklearn.covariance import EllipticEnvelope
from sklearn.svm import OneClassSVM
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns

# For Autoencoder
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.optimizers import Adam

# ------------------ Load features ------------------
X = np.load("data/features/geshika_features.npy")

# ------------------ Scale features ------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ------------------ Train/Test split ------------------
X_train, X_test = train_test_split(X_scaled, test_size=0.3, random_state=42)

# ------------------ Train & score models ------------------
score_samples_dict = {}

# 1️⃣ Isolation Forest
iso = IsolationForest(contamination=0.1, random_state=42)
iso.fit(X_train)
score_samples_dict["IsolationForest"] = iso.score_samples(X_test)

# 2️⃣ LOF (Novelty mode)
lof = LocalOutlierFactor(n_neighbors=20, novelty=True)
lof.fit(X_train)
score_samples_dict["LOF"] = lof.score_samples(X_test)

# 3️⃣ GMM
gmm = GaussianMixture(n_components=1, covariance_type='full', random_state=42)
gmm.fit(X_train)
score_samples_dict["GMM"] = gmm.score_samples(X_test)

# 4️⃣ Elliptic Envelope
ee = EllipticEnvelope(contamination=0.1, random_state=42)
ee.fit(X_train)
score_samples_dict["EllipticEnvelope"] = ee.decision_function(X_test)

# 5️⃣ One-Class SVM
ocsvm = OneClassSVM(kernel='rbf', gamma='scale', nu=0.15)
ocsvm.fit(X_train)
score_samples_dict["OneClassSVM"] = ocsvm.score_samples(X_test)

# 6️⃣ Autoencoder
input_dim = X_train.shape[1]
encoding_dim = 8

# Build simple AE
input_layer = Input(shape=(input_dim,))
encoded = Dense(encoding_dim, activation='relu')(input_layer)
decoded = Dense(input_dim, activation='linear')(encoded)
autoencoder = Model(inputs=input_layer, outputs=decoded)
autoencoder.compile(optimizer=Adam(learning_rate=0.01), loss='mse')

# Train AE only on normal user behavior
autoencoder.fit(X_train, X_train, epochs=100, batch_size=8, verbose=0)

# Compute reconstruction error
reconstructions = autoencoder.predict(X_test)
recon_error = np.mean((X_test - reconstructions) ** 2, axis=1)

# Convert reconstruction error to "score" (higher = better normality)
ae_scores = -recon_error
score_samples_dict["Autoencoder"] = ae_scores

# ------------------ Raw mean scores ------------------
raw_scores = {model: scores.mean() for model, scores in score_samples_dict.items()}
print("\n📊 Raw Mean Scores per Model\n")
for model, score in raw_scores.items():
    print(f"{model:20s}: {score:.4f}")

# ------------------ Normalization (exclude EE to prevent skew) ------------------
models_for_norm = ["IsolationForest", "LOF", "GMM", "OneClassSVM", "Autoencoder"]
norm_values = np.array([raw_scores[m] for m in models_for_norm]).reshape(-1,1)
norm_scaler = MinMaxScaler()
normalized = norm_scaler.fit_transform(norm_values).flatten()

print("\n📊 Normalized Scores (Excluding EE)\n")
for model, score in zip(models_for_norm, normalized):
    print(f"{model:20s}: {score:.4f}")

# ------------------ Visualization ------------------
plt.figure(figsize=(20,5))

# -------- Boxplot --------
plt.subplot(1,3,1)
plt.boxplot(
    [score_samples_dict[m] for m in score_samples_dict],
    labels=list(score_samples_dict.keys()),
    patch_artist=True,
    boxprops=dict(facecolor='skyblue', alpha=0.6),
    medianprops=dict(color='red', linewidth=2)
)
plt.ylabel("Normality Score")
plt.title("Boxplot of Model Scores")
plt.grid(axis='y', linestyle='--', alpha=0.7)

# -------- KDE / Density Plot --------
plt.subplot(1,3,2)
for model, scores_arr in score_samples_dict.items():
    sns.kdeplot(scores_arr, label=model, fill=True, alpha=0.4)
plt.xlabel("Normality Score")
plt.ylabel("Density")
plt.title("KDE of Model Scores")
plt.legend()

# -------- PCA Scatter --------
plt.subplot(1,3,3)
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
plt.scatter(X_pca[:,0], X_pca[:,1], alpha=0.6, s=50, color='skyblue', edgecolor='k')
plt.title("PCA of 14-D Feature Space")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.grid(True)

plt.tight_layout()
plt.show()
