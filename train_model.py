import os
import pandas as pd
from google.cloud import bigquery
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, accuracy_score
import joblib

def train_model():
    client = bigquery.Client()

    # We only care about sessions where users actually added something to their cart
    query = """
    SELECT 
        total_views,
        total_carts,
        TIMESTAMP_DIFF(session_end, session_start, MINUTE) as session_duration_minutes,
        experiment_group,
        CASE WHEN total_purchases = 0 THEN 1 ELSE 0 END as abandoned_cart
    FROM `gen-lang-client-0874026413.cosmetics_gold.fact_user_sessions`
    WHERE total_carts > 0
    """

    print("Fetching training data from BigQuery...")
    df = client.query(query).to_dataframe()
    
    X = df[['total_views', 'total_carts', 'session_duration_minutes', 'experiment_group']]
    y = df['abandoned_cart']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"Training XGBoost model on {len(X_train)} samples...")
    # Initialize XGBoost classifier
    # Optimized for ROC-AUC
    model = xgb.XGBClassifier(
        n_estimators=100, 
        max_depth=4, 
        learning_rate=0.1, 
        eval_metric='auc',
        random_state=42,
        use_label_encoder=False
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    print("\n--- Model Evaluation ---")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"ROC-AUC: {roc_auc_score(y_test, y_pred_proba):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Serialize model
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/xgb_model.pkl')
    # Save a sample of X_train to disk for the SHAP explainer later
    X_train.sample(1000, random_state=42).to_csv('models/X_train_sample.csv', index=False)
    print("Model saved to models/xgb_model.pkl")

if __name__ == "__main__":
    train_model()
