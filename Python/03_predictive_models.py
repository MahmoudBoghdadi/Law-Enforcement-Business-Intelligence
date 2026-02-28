import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix, 
                             mean_squared_error, r2_score, accuracy_score)
from sklearn.cluster import DBSCAN
import joblib
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("CHICAGO CRIME ANALYTICS - PREDICTIVE MODELING")
print("="*70)

# Load cleaned data
print("\n[1/5] Loading cleaned data...")
df = pd.read_csv('data/processed/chicago_crime_clean.csv')
df['date'] = pd.to_datetime(df['date'])
print(f"✓ Loaded {len(df):,} records")

# ====================================
# MODEL 1: CRIME TYPE PREDICTION
# ====================================

print("\n" + "="*70)
print("MODEL 1: CRIME TYPE PREDICTION")
print("="*70)

print("\nPreparing features for crime type classification...")


top_crimes = df['primary_type'].value_counts().head(5).index
model1_data = df[df['primary_type'].isin(top_crimes)].copy()

print(f"Training on top 5 crime types: {list(top_crimes)}")
print(f"Training samples: {len(model1_data):,}")


features = ['hour', 'day_of_week', 'month', 'is_weekend', 'severity_level']
X = model1_data[features]
y = model1_data['primary_type']

le = LabelEncoder()
y_encoded = le.fit_transform(y)


X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)


scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"\nTrain set: {len(X_train):,} | Test set: {len(X_test):,}")

print("\nTraining Random Forest Classifier...")
rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    min_samples_split=10,
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train_scaled, y_train)

y_pred = rf_model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)

print(f"\nModel Performance:")
print(f"Accuracy: {accuracy:.2%}")
print(f"\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_))


feature_importance = pd.DataFrame({
    'Feature': features,
    'Importance': rf_model.feature_importances_
}).sort_values('Importance', ascending=False)

print("\nFeature Importance:")
print(feature_importance.to_string(index=False))

plt.figure(figsize=(10, 8))
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=le.classes_, yticklabels=le.classes_)
plt.title('Crime Type Prediction - Confusion Matrix', fontsize=14, fontweight='bold')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.tight_layout()
plt.savefig('docs/screenshots/crime_type_confusion_matrix.png', dpi=300)
plt.close()


joblib.dump(rf_model, 'models/crime_type_classifier.pkl')
joblib.dump(scaler, 'models/crime_type_scaler.pkl')
joblib.dump(le, 'models/crime_type_encoder.pkl')


# ====================================
# MODEL 2: CRIME VOLUME FORECASTING
# ====================================

print("\n" + "="*70)
print("MODEL 2: DAILY CRIME VOLUME FORECASTING")
print("="*70)

daily_crimes = df.groupby(df['date'].dt.date).size().reset_index()
daily_crimes.columns = ['date', 'crime_count']
daily_crimes['date'] = pd.to_datetime(daily_crimes['date'])

print(f"Daily records: {len(daily_crimes):,}")


daily_crimes['day_of_year'] = daily_crimes['date'].dt.dayofyear
daily_crimes['day_of_week'] = daily_crimes['date'].dt.dayofweek
daily_crimes['month'] = daily_crimes['date'].dt.month
daily_crimes['week'] = daily_crimes['date'].dt.isocalendar().week
daily_crimes['is_weekend'] = daily_crimes['day_of_week'].isin([5, 6]).astype(int)


for lag in [1, 7, 14, 30]:
    daily_crimes[f'lag_{lag}'] = daily_crimes['crime_count'].shift(lag)

daily_crimes['rolling_mean_7'] = daily_crimes['crime_count'].rolling(7).mean()
daily_crimes['rolling_std_7'] = daily_crimes['crime_count'].rolling(7).std()
daily_crimes['rolling_mean_30'] = daily_crimes['crime_count'].rolling(30).mean()


daily_crimes = daily_crimes.dropna()

print(f"After feature engineering: {len(daily_crimes):,} records")


forecast_features = [
    'day_of_year', 'day_of_week', 'month', 'week', 'is_weekend',
    'lag_1', 'lag_7', 'lag_14', 'lag_30',
    'rolling_mean_7', 'rolling_std_7', 'rolling_mean_30'
]

X_forecast = daily_crimes[forecast_features]
y_forecast = daily_crimes['crime_count']


split_idx = int(len(X_forecast) * 0.8)
X_train_f = X_forecast.iloc[:split_idx]
X_test_f = X_forecast.iloc[split_idx:]
y_train_f = y_forecast.iloc[:split_idx]
y_test_f = y_forecast.iloc[split_idx:]

print(f"\nTrain set: {len(X_train_f)} days | Test set: {len(X_test_f)} days")


print("\nTraining Gradient Boosting Regressor...")
gb_model = GradientBoostingRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=5,
    random_state=42
)
gb_model.fit(X_train_f, y_train_f)

y_pred_f = gb_model.predict(X_test_f)

rmse = np.sqrt(mean_squared_error(y_test_f, y_pred_f))
r2 = r2_score(y_test_f, y_pred_f)
mape = np.mean(np.abs((y_test_f - y_pred_f) / y_test_f)) * 100

print(f"\nModel Performance:")
print(f"RMSE: {rmse:.2f} crimes/day")
print(f"R² Score: {r2:.2%}")
print(f"MAPE: {mape:.2f}%")

plt.figure(figsize=(15, 6))
test_dates = daily_crimes['date'].iloc[split_idx:].values
plt.plot(test_dates, y_test_f.values, label='Actual', marker='o', markersize=3, linewidth=2)
plt.plot(test_dates, y_pred_f, label='Predicted', marker='o', markersize=3, linewidth=2, alpha=0.7)
plt.title('Daily Crime Volume Forecasting - Actual vs Predicted', fontsize=14, fontweight='bold')
plt.xlabel('Date')
plt.ylabel('Daily Crime Count')
plt.legend()
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('docs/screenshots/crime_forecast.png', dpi=300)
plt.close()

joblib.dump(gb_model, 'models/crime_forecast_model.pkl')


# ====================================
# MODEL 3: HOTSPOT DETECTION (CLUSTERING)
# ====================================

print("\n" + "="*70)
print("MODEL 3: CRIME HOTSPOT DETECTION")
print("="*70)

recent_crimes = df[df['has_valid_coords']].tail(100000) 
coords = recent_crimes[['latitude', 'longitude']].values

print(f"Analyzing {len(coords):,} crime locations")


dbscan = DBSCAN(eps=0.01, min_samples=20)
clusters = dbscan.fit_predict(coords)

recent_crimes['cluster'] = clusters

hotspots = recent_crimes[recent_crimes['cluster'] != -1].groupby('cluster').agg({
    'latitude': 'mean',
    'longitude': 'mean',
    'id': 'count',
    'severity_level': 'mean'
}).round(4)
hotspots.columns = ['Center_Lat', 'Center_Lon', 'Crime_Count', 'Avg_Severity']
hotspots = hotspots.sort_values('Crime_Count', ascending=False)

print(f"\nIdentified {len(hotspots)} crime hotspots")
print(f"Outliers (not in clusters): {(clusters == -1).sum():,}")

print("\nTop 10 Hotspots:")
print(hotspots.head(10).to_string())

plt.figure(figsize=(12, 10))
scatter = plt.scatter(
    recent_crimes['longitude'],
    recent_crimes['latitude'],
    c=recent_crimes['cluster'],
    cmap='tab20',
    alpha=0.5,
    s=10
)

plt.scatter(
    hotspots['Center_Lon'],
    hotspots['Center_Lat'],
    c='red',
    marker='X',
    s=200,
    edgecolors='black',
    linewidths=2,
    label='Hotspot Centers',
    zorder=5
)

plt.title('Crime Hotspot Detection using DBSCAN Clustering', fontsize=14, fontweight='bold')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.legend()
plt.colorbar(scatter, label='Cluster ID')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('docs/screenshots/crime_hotspots.png', dpi=300)
plt.close()


hotspots.to_csv('data/output/crime_hotspots.csv')
joblib.dump(dbscan, 'models/hotspot_detector.pkl')

# ====================================
# MODEL SUMMARY
# ====================================

print("\n" + "="*70)
print("PREDICTIVE MODELING COMPLETE")
print("="*70)

model_summary = {
    'Crime Type Classifier': {
        'Algorithm': 'Random Forest',
        'Accuracy': f"{accuracy:.2%}",
        'Use Case': 'Predict likely crime type based on temporal features'
    },
    'Crime Volume Forecaster': {
        'Algorithm': 'Gradient Boosting',
        'R² Score': f"{r2:.2%}",
        'RMSE': f"{rmse:.2f} crimes/day",
        'Use Case': 'Forecast daily crime volume for resource planning'
    },
    'Hotspot Detector': {
        'Algorithm': 'DBSCAN Clustering',
        'Hotspots Found': len(hotspots),
        'Use Case': 'Identify geographic areas requiring increased patrols'
    }
}

print("\nModel Summary:")
for model_name, metrics in model_summary.items():
    print(f"\n{model_name}:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value}")