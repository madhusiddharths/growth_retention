import base64
import io
import pandas as pd
import joblib
import shap
import matplotlib.pyplot as plt
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Cart Abandonment Predictor")

model = joblib.load('models/xgb_model.pkl')
X_sample = pd.read_csv('models/X_train_sample.csv')
explainer = shap.TreeExplainer(model)

class PredictionRequest(BaseModel):
    total_views: float
    total_carts: float
    session_duration_minutes: float
    experiment_group: float

@app.post("/predict")
def predict(request: PredictionRequest):
    df = pd.DataFrame([request.model_dump()])
    
    prob = model.predict_proba(df)[0][1]
    
    shap_values = explainer.shap_values(df)
    explanation = shap.Explanation(
        values=shap_values[0], 
        base_values=explainer.expected_value, 
        data=df.iloc[0].values,
        feature_names=df.columns
    )
    
    plt.figure()
    shap.waterfall_plot(explanation, show=False)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight')
    plt.close()
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    
    return {
        "abandonment_probability": float(prob),
        "shap_plot_b64": img_b64
    }

class BulkPredictionRequest(BaseModel):
    sessions: List[PredictionRequest]

@app.post("/bulk_predict")
def bulk_predict(request: BulkPredictionRequest):
    if not request.sessions:
        return {"predictions": []}
    df = pd.DataFrame([s.model_dump() for s in request.sessions])
    probs = model.predict_proba(df)[:, 1]
    return {"predictions": probs.tolist()}
