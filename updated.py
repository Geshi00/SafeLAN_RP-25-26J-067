import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.mixture import GaussianMixture
from sklearn.covariance import EllipticEnvelope
from sklearn.svm import OneClassSVM
from sklearn.decomposition import PCA
from sklearn.metrics import (
    roc_curve, auc, precision_recall_curve, 
    confusion_matrix, classification_report,
    f1_score, precision_score, recall_score
)
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# For Autoencoder (using sklearn instead of TensorFlow)
from sklearn.neural_network import MLPRegressor

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)

# ==================== CONFIGURATION ====================
CONFIG = {
    'test_size': 0.4,
    'random_state': 42,
    'contamination': 0.1,  # Expected percentage of outliers
    'cv_folds': 5,
    'n_impostor_samples': 100,  # Generate synthetic impostor samples
}

# ==================== LOAD FEATURES ====================
print("=" * 80)
print("KEYSTROKE AUTHENTICATION SYSTEM - ENHANCED EVALUATION")
print("=" * 80)

X_genuine = np.load("data/features/geshika_features.npy")
print(f"\n✓ Loaded {X_genuine.shape[0]} genuine samples with {X_genuine.shape[1]} features")

# ==================== GENERATE IMPOSTOR SAMPLES ====================
print(f"\n🔧 Generating {CONFIG['n_impostor_samples']} synthetic impostor samples...")

# Method 1: Add noise to genuine samples
noise_samples = X_genuine[np.random.choice(X_genuine.shape[0], CONFIG['n_impostor_samples']//2)]
noise_samples += np.random.normal(0, np.std(X_genuine) * 0.5, noise_samples.shape)

# Method 2: Random permutation of features
perm_samples = X_genuine[np.random.choice(X_genuine.shape[0], CONFIG['n_impostor_samples']//2)]
for i in range(perm_samples.shape[0]):
    perm_indices = np.random.permutation(perm_samples.shape[1])
    perm_samples[i] = perm_samples[i][perm_indices]

X_impostor = np.vstack([noise_samples, perm_samples])

# Create labels (1 = genuine, 0 = impostor)
y_genuine = np.ones(X_genuine.shape[0])
y_impostor = np.zeros(X_impostor.shape[0])

X_all = np.vstack([X_genuine, X_impostor])
y_all = np.hstack([y_genuine, y_impostor])

print(f"✓ Total dataset: {X_all.shape[0]} samples ({X_genuine.shape[0]} genuine, {X_impostor.shape[0]} impostor)")

# ==================== SCALE FEATURES ====================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_all)

# ==================== TRAIN/TEST SPLIT ====================
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_all, 
    test_size=CONFIG['test_size'], 
    random_state=CONFIG['random_state'],
    stratify=y_all
)

# Separate genuine training data for one-class models
X_train_genuine = X_train[y_train == 1]
X_train_impostor = X_train[y_train == 0]

print(f"\n📊 Train set: {X_train.shape[0]} samples ({np.sum(y_train==1):.0f} genuine, {np.sum(y_train==0):.0f} impostor)")
print(f"📊 Test set:  {X_test.shape[0]} samples ({np.sum(y_test==1):.0f} genuine, {np.sum(y_test==0):.0f} impostor)")

# ==================== HYPERPARAMETER OPTIMIZATION ====================
print("\n" + "=" * 80)
print("HYPERPARAMETER OPTIMIZATION")
print("=" * 80)

best_params = {}

# 1. Isolation Forest
print("\n🔍 Optimizing Isolation Forest...")
iso_params = {
    'contamination': [0.05, 0.1, 0.15, 0.2],
    'n_estimators': [50, 100, 150],
    'max_samples': ['auto', 0.5, 0.7]
}

best_iso_score = -np.inf
for cont in iso_params['contamination']:
    for n_est in iso_params['n_estimators']:
        for max_samp in iso_params['max_samples']:
            iso = IsolationForest(
                contamination=cont, 
                n_estimators=n_est, 
                max_samples=max_samp,
                random_state=CONFIG['random_state']
            )
            iso.fit(X_train_genuine)
            scores = iso.score_samples(X_test)
            predictions = iso.predict(X_test)
            predictions = np.where(predictions == 1, 1, 0)  # 1=normal, -1=outlier -> 1=genuine, 0=impostor
            f1 = f1_score(y_test, predictions)
            
            if f1 > best_iso_score:
                best_iso_score = f1
                best_params['IsolationForest'] = {
                    'contamination': cont, 
                    'n_estimators': n_est, 
                    'max_samples': max_samp,
                    'f1_score': f1
                }

print(f"   Best params: {best_params['IsolationForest']}")

# 2. LOF
print("\n🔍 Optimizing Local Outlier Factor...")
lof_params = {
    'n_neighbors': [10, 20, 30, 40],
    'contamination': [0.05, 0.1, 0.15, 0.2]
}

best_lof_score = -np.inf
for n_neigh in lof_params['n_neighbors']:
    for cont in lof_params['contamination']:
        lof = LocalOutlierFactor(
            n_neighbors=n_neigh, 
            contamination=cont,
            novelty=True
        )
        lof.fit(X_train_genuine)
        scores = lof.score_samples(X_test)
        predictions = lof.predict(X_test)
        predictions = np.where(predictions == 1, 1, 0)
        f1 = f1_score(y_test, predictions)
        
        if f1 > best_lof_score:
            best_lof_score = f1
            best_params['LOF'] = {
                'n_neighbors': n_neigh,
                'contamination': cont,
                'f1_score': f1
            }

print(f"   Best params: {best_params['LOF']}")

# 3. One-Class SVM
print("\n🔍 Optimizing One-Class SVM...")
ocsvm_params = {
    'kernel': ['rbf', 'poly', 'sigmoid'],
    'gamma': ['scale', 'auto', 0.001, 0.01, 0.1],
    'nu': [0.05, 0.1, 0.15, 0.2]
}

best_ocsvm_score = -np.inf
for kernel in ocsvm_params['kernel']:
    for gamma in ocsvm_params['gamma']:
        for nu in ocsvm_params['nu']:
            try:
                ocsvm = OneClassSVM(kernel=kernel, gamma=gamma, nu=nu)
                ocsvm.fit(X_train_genuine)
                predictions = ocsvm.predict(X_test)
                predictions = np.where(predictions == 1, 1, 0)
                f1 = f1_score(y_test, predictions)
                
                if f1 > best_ocsvm_score:
                    best_ocsvm_score = f1
                    best_params['OneClassSVM'] = {
                        'kernel': kernel,
                        'gamma': gamma,
                        'nu': nu,
                        'f1_score': f1
                    }
            except:
                continue

print(f"   Best params: {best_params['OneClassSVM']}")

# ==================== TRAIN OPTIMIZED MODELS ====================
print("\n" + "=" * 80)
print("TRAINING OPTIMIZED MODELS")
print("=" * 80)

models = {}
score_samples_dict = {}
predictions_dict = {}

# 1. Isolation Forest (optimized)
print("\n🤖 Training Isolation Forest...")
iso = IsolationForest(
    contamination=best_params['IsolationForest']['contamination'],
    n_estimators=best_params['IsolationForest']['n_estimators'],
    max_samples=best_params['IsolationForest']['max_samples'],
    random_state=CONFIG['random_state']
)
iso.fit(X_train_genuine)
models['IsolationForest'] = iso
score_samples_dict['IsolationForest'] = iso.score_samples(X_test)
predictions_dict['IsolationForest'] = np.where(iso.predict(X_test) == 1, 1, 0)

# 2. LOF (optimized)
print("🤖 Training Local Outlier Factor...")
lof = LocalOutlierFactor(
    n_neighbors=best_params['LOF']['n_neighbors'],
    contamination=best_params['LOF']['contamination'],
    novelty=True
)
lof.fit(X_train_genuine)
models['LOF'] = lof
score_samples_dict['LOF'] = lof.score_samples(X_test)
predictions_dict['LOF'] = np.where(lof.predict(X_test) == 1, 1, 0)

# 3. GMM
print("🤖 Training Gaussian Mixture Model...")
gmm = GaussianMixture(n_components=1, covariance_type='full', random_state=CONFIG['random_state'])
gmm.fit(X_train_genuine)
models['GMM'] = gmm
score_samples_dict['GMM'] = gmm.score_samples(X_test)
# GMM: threshold at percentile
gmm_threshold = np.percentile(gmm.score_samples(X_train_genuine), CONFIG['contamination'] * 100)
predictions_dict['GMM'] = np.where(score_samples_dict['GMM'] >= gmm_threshold, 1, 0)

# 4. Elliptic Envelope
print("🤖 Training Elliptic Envelope...")
ee = EllipticEnvelope(contamination=CONFIG['contamination'], random_state=CONFIG['random_state'])
ee.fit(X_train_genuine)
models['EllipticEnvelope'] = ee
score_samples_dict['EllipticEnvelope'] = ee.decision_function(X_test)
predictions_dict['EllipticEnvelope'] = np.where(ee.predict(X_test) == 1, 1, 0)

# 5. One-Class SVM (optimized)
print("🤖 Training One-Class SVM...")
ocsvm = OneClassSVM(
    kernel=best_params['OneClassSVM']['kernel'],
    gamma=best_params['OneClassSVM']['gamma'],
    nu=best_params['OneClassSVM']['nu']
)
ocsvm.fit(X_train_genuine)
models['OneClassSVM'] = ocsvm
score_samples_dict['OneClassSVM'] = ocsvm.score_samples(X_test)
predictions_dict['OneClassSVM'] = np.where(ocsvm.predict(X_test) == 1, 1, 0)

# 6. Autoencoder (using MLPRegressor)
print("🤖 Training Autoencoder...")
input_dim = X_train_genuine.shape[1]
encoding_dim = 8

# Create autoencoder using MLPRegressor
autoencoder = MLPRegressor(
    hidden_layer_sizes=(16, encoding_dim, 16),
    activation='relu',
    solver='adam',
    learning_rate_init=0.001,
    max_iter=200,
    early_stopping=True,
    validation_fraction=0.2,
    n_iter_no_change=10,
    random_state=CONFIG['random_state'],
    verbose=False
)

autoencoder.fit(X_train_genuine, X_train_genuine)

models['Autoencoder'] = autoencoder
reconstructions = autoencoder.predict(X_test)
recon_error = np.mean((X_test - reconstructions) ** 2, axis=1)
score_samples_dict['Autoencoder'] = -recon_error

# Autoencoder: threshold at training reconstruction error percentile
train_reconstructions = autoencoder.predict(X_train_genuine)
train_recon_error = np.mean((X_train_genuine - train_reconstructions) ** 2, axis=1)
ae_threshold = np.percentile(train_recon_error, (1 - CONFIG['contamination']) * 100)
predictions_dict['Autoencoder'] = np.where(recon_error <= ae_threshold, 1, 0)

print("\n✓ All models trained successfully!")

# ==================== EVALUATION METRICS ====================
print("\n" + "=" * 80)
print("EVALUATION METRICS")
print("=" * 80)

results = []

for model_name in models.keys():
    y_pred = predictions_dict[model_name]
    
    # Calculate metrics
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    # FAR (False Acceptance Rate) = FP / (FP + TN)
    far = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    # FRR (False Rejection Rate) = FN / (FN + TP)
    frr = fn / (fn + tp) if (fn + tp) > 0 else 0
    
    # EER approximation
    eer = (far + frr) / 2
    
    results.append({
        'Model': model_name,
        'Accuracy': accuracy,
        'Precision': precision,
        'Recall': recall,
        'F1-Score': f1,
        'FAR': far,
        'FRR': frr,
        'EER': eer,
        'TP': tp,
        'TN': tn,
        'FP': fp,
        'FN': fn
    })

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('F1-Score', ascending=False)

print("\n" + results_df.to_string(index=False))

# Save results
results_df.to_csv('evaluation_results.csv', index=False)
print("\n✓ Results saved to evaluation_results.csv")

# ==================== DETAILED CLASSIFICATION REPORTS ====================
print("\n" + "=" * 80)
print("DETAILED CLASSIFICATION REPORTS")
print("=" * 80)

for model_name in models.keys():
    print(f"\n{'='*40}")
    print(f"{model_name}")
    print(f"{'='*40}")
    print(classification_report(
        y_test, 
        predictions_dict[model_name],
        target_names=['Impostor', 'Genuine'],
        zero_division=0
    ))

# ==================== VISUALIZATIONS ====================
print("\n" + "=" * 80)
print("GENERATING VISUALIZATIONS")
print("=" * 80)

# ==================== FIGURE 1: ROC CURVES ====================
fig1 = plt.figure(figsize=(20, 12))

# ROC Curves
plt.subplot(2, 3, 1)
for model_name, scores in score_samples_dict.items():
    # Normalize scores to [0, 1]
    scores_norm = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    fpr, tpr, _ = roc_curve(y_test, scores_norm)
    roc_auc = auc(fpr, tpr)
    plt.plot(fpr, tpr, linewidth=2, label=f'{model_name} (AUC = {roc_auc:.3f})')

plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random')
plt.xlabel('False Positive Rate (FAR)', fontsize=12)
plt.ylabel('True Positive Rate (1 - FRR)', fontsize=12)
plt.title('ROC Curves - All Models', fontsize=14, fontweight='bold')
plt.legend(loc='lower right', fontsize=10)
plt.grid(True, alpha=0.3)

# Precision-Recall Curves
plt.subplot(2, 3, 2)
for model_name, scores in score_samples_dict.items():
    scores_norm = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    precision, recall, _ = precision_recall_curve(y_test, scores_norm)
    pr_auc = auc(recall, precision)
    plt.plot(recall, precision, linewidth=2, label=f'{model_name} (AUC = {pr_auc:.3f})')

plt.xlabel('Recall', fontsize=12)
plt.ylabel('Precision', fontsize=12)
plt.title('Precision-Recall Curves', fontsize=14, fontweight='bold')
plt.legend(loc='lower left', fontsize=10)
plt.grid(True, alpha=0.3)

# Performance Metrics Comparison
plt.subplot(2, 3, 3)
metrics_to_plot = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
x = np.arange(len(results_df))
width = 0.2

for i, metric in enumerate(metrics_to_plot):
    plt.bar(x + i * width, results_df[metric], width, label=metric, alpha=0.8)

plt.xlabel('Models', fontsize=12)
plt.ylabel('Score', fontsize=12)
plt.title('Performance Metrics Comparison', fontsize=14, fontweight='bold')
plt.xticks(x + width * 1.5, results_df['Model'], rotation=45, ha='right')
plt.legend(fontsize=10)
plt.ylim(0, 1.1)
plt.grid(axis='y', alpha=0.3)

# FAR vs FRR
plt.subplot(2, 3, 4)
x = np.arange(len(results_df))
width = 0.35

plt.bar(x - width/2, results_df['FAR'], width, label='FAR', color='salmon', alpha=0.8)
plt.bar(x + width/2, results_df['FRR'], width, label='FRR', color='lightblue', alpha=0.8)

plt.xlabel('Models', fontsize=12)
plt.ylabel('Error Rate', fontsize=12)
plt.title('False Acceptance Rate vs False Rejection Rate', fontsize=14, fontweight='bold')
plt.xticks(x, results_df['Model'], rotation=45, ha='right')
plt.legend(fontsize=10)
plt.grid(axis='y', alpha=0.3)

# EER Comparison
plt.subplot(2, 3, 5)
colors = plt.cm.RdYlGn_r(results_df['EER'] / results_df['EER'].max())
bars = plt.bar(results_df['Model'], results_df['EER'], color=colors, alpha=0.8, edgecolor='black')

plt.xlabel('Models', fontsize=12)
plt.ylabel('Equal Error Rate (EER)', fontsize=12)
plt.title('Equal Error Rate (Lower is Better)', fontsize=14, fontweight='bold')
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.3f}',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

# F1-Score Ranking
plt.subplot(2, 3, 6)
colors = plt.cm.RdYlGn(results_df['F1-Score'] / results_df['F1-Score'].max())
bars = plt.barh(results_df['Model'], results_df['F1-Score'], color=colors, alpha=0.8, edgecolor='black')

plt.xlabel('F1-Score', fontsize=12)
plt.ylabel('Models', fontsize=12)
plt.title('Model Ranking by F1-Score', fontsize=14, fontweight='bold')
plt.xlim(0, 1)
plt.grid(axis='x', alpha=0.3)

# Add value labels
for i, (bar, score) in enumerate(zip(bars, results_df['F1-Score'])):
    plt.text(score + 0.02, bar.get_y() + bar.get_height()/2,
            f'{score:.3f}',
            ha='left', va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('evaluation_metrics.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: evaluation_metrics.png")

# ==================== FIGURE 2: CONFUSION MATRICES ====================
fig2 = plt.figure(figsize=(20, 12))

for idx, model_name in enumerate(models.keys(), 1):
    plt.subplot(2, 3, idx)
    cm = confusion_matrix(y_test, predictions_dict[model_name])
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
                xticklabels=['Impostor', 'Genuine'],
                yticklabels=['Impostor', 'Genuine'],
                annot_kws={'fontsize': 14, 'fontweight': 'bold'})
    
    plt.title(f'{model_name}', fontsize=14, fontweight='bold')
    plt.ylabel('True Label', fontsize=12)
    plt.xlabel('Predicted Label', fontsize=12)
    
    # Add accuracy in subtitle
    accuracy = (cm[0,0] + cm[1,1]) / cm.sum()
    plt.text(0.5, -0.15, f'Accuracy: {accuracy:.3f}', 
             ha='center', transform=plt.gca().transAxes, fontsize=11)

plt.tight_layout()
plt.savefig('confusion_matrices.png', dpi=300, bbox_inches='tight')
print("✓ Saved: confusion_matrices.png")

# ==================== FIGURE 3: SCORE DISTRIBUTIONS ====================
fig3 = plt.figure(figsize=(20, 15))

for idx, model_name in enumerate(models.keys(), 1):
    plt.subplot(3, 2, idx)
    
    scores = score_samples_dict[model_name]
    scores_genuine = scores[y_test == 1]
    scores_impostor = scores[y_test == 0]
    
    # KDE plots
    sns.kdeplot(scores_genuine, label='Genuine', fill=True, alpha=0.5, color='green', linewidth=2)
    sns.kdeplot(scores_impostor, label='Impostor', fill=True, alpha=0.5, color='red', linewidth=2)
    
    plt.xlabel('Normality Score', fontsize=12)
    plt.ylabel('Density', fontsize=12)
    plt.title(f'{model_name} - Score Distribution', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    
    # Add separation info
    separation = np.abs(scores_genuine.mean() - scores_impostor.mean())
    plt.text(0.05, 0.95, f'Separation: {separation:.3f}', 
             transform=plt.gca().transAxes, fontsize=10,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('score_distributions.png', dpi=300, bbox_inches='tight')
print("✓ Saved: score_distributions.png")

# ==================== FIGURE 4: PCA & FEATURE SPACE ====================
fig4 = plt.figure(figsize=(20, 12))

# PCA 2D
plt.subplot(2, 3, 1)
pca_2d = PCA(n_components=2)
X_pca_2d = pca_2d.fit_transform(X_scaled)

genuine_mask = y_all == 1
plt.scatter(X_pca_2d[genuine_mask, 0], X_pca_2d[genuine_mask, 1], 
           c='green', alpha=0.6, s=50, label='Genuine', edgecolor='k', linewidth=0.5)
plt.scatter(X_pca_2d[~genuine_mask, 0], X_pca_2d[~genuine_mask, 1], 
           c='red', alpha=0.6, s=50, label='Impostor', edgecolor='k', linewidth=0.5)

plt.xlabel(f'PC1 ({pca_2d.explained_variance_ratio_[0]:.2%} variance)', fontsize=12)
plt.ylabel(f'PC2 ({pca_2d.explained_variance_ratio_[1]:.2%} variance)', fontsize=12)
plt.title('PCA 2D Projection', fontsize=14, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)

# PCA 3D
from mpl_toolkits.mplot3d import Axes3D
ax = fig4.add_subplot(2, 3, 2, projection='3d')

pca_3d = PCA(n_components=3)
X_pca_3d = pca_3d.fit_transform(X_scaled)

ax.scatter(X_pca_3d[genuine_mask, 0], X_pca_3d[genuine_mask, 1], X_pca_3d[genuine_mask, 2],
          c='green', alpha=0.6, s=30, label='Genuine', edgecolor='k', linewidth=0.3)
ax.scatter(X_pca_3d[~genuine_mask, 0], X_pca_3d[~genuine_mask, 1], X_pca_3d[~genuine_mask, 2],
          c='red', alpha=0.6, s=30, label='Impostor', edgecolor='k', linewidth=0.3)

ax.set_xlabel(f'PC1 ({pca_3d.explained_variance_ratio_[0]:.2%})', fontsize=10)
ax.set_ylabel(f'PC2 ({pca_3d.explained_variance_ratio_[1]:.2%})', fontsize=10)
ax.set_zlabel(f'PC3 ({pca_3d.explained_variance_ratio_[2]:.2%})', fontsize=10)
ax.set_title('PCA 3D Projection', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)

# Explained Variance
plt.subplot(2, 3, 3)
pca_full = PCA()
pca_full.fit(X_scaled)
cumsum_variance = np.cumsum(pca_full.explained_variance_ratio_)

plt.plot(range(1, len(cumsum_variance) + 1), cumsum_variance, 'bo-', linewidth=2, markersize=8)
plt.axhline(y=0.95, color='r', linestyle='--', linewidth=2, label='95% threshold')
plt.xlabel('Number of Components', fontsize=12)
plt.ylabel('Cumulative Explained Variance', fontsize=12)
plt.title('PCA Explained Variance', fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.legend(fontsize=11)

# Feature Correlation Heatmap
plt.subplot(2, 3, 4)
feature_names = [f'F{i+1}' for i in range(X_genuine.shape[1])]
corr_matrix = np.corrcoef(X_genuine.T)

sns.heatmap(corr_matrix, cmap='coolwarm', center=0, 
           xticklabels=feature_names, yticklabels=feature_names,
           cbar_kws={'label': 'Correlation'}, square=True)
plt.title('Feature Correlation Matrix', fontsize=14, fontweight='bold')

# Box plot of features
plt.subplot(2, 3, 5)
feature_data = []
for i in range(min(10, X_genuine.shape[1])):  # Show first 10 features
    feature_data.append(X_genuine[:, i])

bp = plt.boxplot(feature_data, labels=[f'F{i+1}' for i in range(len(feature_data))],
                patch_artist=True)

for patch in bp['boxes']:
    patch.set_facecolor('skyblue')
    patch.set_alpha(0.7)

plt.ylabel('Feature Value', fontsize=12)
plt.xlabel('Features', fontsize=12)
plt.title('Feature Distribution (First 10 Features)', fontsize=14, fontweight='bold')
plt.grid(axis='y', alpha=0.3)

# Autoencoder Loss Curve
plt.subplot(2, 3, 6)

# Since we're using sklearn MLPRegressor, we'll plot the loss curve from its internal history
if hasattr(autoencoder, 'loss_curve_'):
    plt.plot(autoencoder.loss_curve_, label='Training Loss', linewidth=2, color='blue')
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('MSE Loss', fontsize=12)
    plt.title('Autoencoder Training History', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
else:
    # Fallback: show reconstruction error distribution
    plt.hist(train_recon_error, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(ae_threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold: {ae_threshold:.4f}')
    plt.xlabel('Reconstruction Error', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Training Reconstruction Error Distribution', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('feature_analysis.png', dpi=300, bbox_inches='tight')
print("✓ Saved: feature_analysis.png")

# ==================== FIGURE 5: THRESHOLD ANALYSIS ====================
fig5 = plt.figure(figsize=(20, 12))

for idx, model_name in enumerate(models.keys(), 1):
    plt.subplot(2, 3, idx)
    
    scores = score_samples_dict[model_name]
    scores_norm = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    
    thresholds = np.linspace(0, 1, 100)
    fars = []
    frrs = []
    
    for threshold in thresholds:
        y_pred_thresh = (scores_norm >= threshold).astype(int)
        cm = confusion_matrix(y_test, y_pred_thresh)
        tn, fp, fn, tp = cm.ravel()
        
        far = fp / (fp + tn) if (fp + tn) > 0 else 0
        frr = fn / (fn + tp) if (fn + tp) > 0 else 0
        
        fars.append(far)
        frrs.append(frr)
    
    fars = np.array(fars)
    frrs = np.array(frrs)
    
    plt.plot(thresholds, fars, 'r-', linewidth=2, label='FAR')
    plt.plot(thresholds, frrs, 'b-', linewidth=2, label='FRR')
    
    # Find EER
    eer_idx = np.argmin(np.abs(fars - frrs))
    eer_threshold = thresholds[eer_idx]
    eer_value = (fars[eer_idx] + frrs[eer_idx]) / 2
    
    plt.plot(eer_threshold, eer_value, 'go', markersize=10, label=f'EER = {eer_value:.3f}')
    plt.axvline(x=eer_threshold, color='g', linestyle='--', alpha=0.5)
    
    plt.xlabel('Threshold', fontsize=12)
    plt.ylabel('Error Rate', fontsize=12)
    plt.title(f'{model_name} - Threshold Analysis', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.ylim(-0.05, 1.05)

plt.tight_layout()
plt.savefig('threshold_analysis.png', dpi=300, bbox_inches='tight')
print("✓ Saved: threshold_analysis.png")

# ==================== SUMMARY ====================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

best_model = results_df.iloc[0]
print(f"\n🏆 Best Model: {best_model['Model']}")
print(f"   ├─ F1-Score: {best_model['F1-Score']:.4f}")
print(f"   ├─ Accuracy: {best_model['Accuracy']:.4f}")
print(f"   ├─ Precision: {best_model['Precision']:.4f}")
print(f"   ├─ Recall: {best_model['Recall']:.4f}")
print(f"   ├─ FAR: {best_model['FAR']:.4f}")
print(f"   ├─ FRR: {best_model['FRR']:.4f}")
print(f"   └─ EER: {best_model['EER']:.4f}")

print("\n📁 Generated Files:")
print("   ├─ evaluation_results.csv")
print("   ├─ evaluation_metrics.png")
print("   ├─ confusion_matrices.png")
print("   ├─ score_distributions.png")
print("   ├─ feature_analysis.png")
print("   └─ threshold_analysis.png")

print("\n✓ Analysis complete!")
print("=" * 80)