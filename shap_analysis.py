import os
import pandas as pd
import shap
import joblib
import matplotlib.pyplot as plt

def run_shap_analysis():
    print("Loading model and sample data...")
    model = joblib.load('models/xgb_model.pkl')
    X_sample = pd.read_csv('models/X_train_sample.csv')
    
    # Initialize the SHAP Explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    
    os.makedirs('plots', exist_ok=True)
    
    # 1. Global Explanation (Summary Plot)
    print("Generating SHAP Summary Plot...")
    plt.figure()
    shap.summary_plot(shap_values, X_sample, show=False)
    plt.tight_layout()
    plt.savefig('plots/shap_summary.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    # 2. Local Explanation (Force Plot / Waterfall)
    print("Generating SHAP Local Explanation Plot for a single user...")
    # Find a user that the model strongly predicts will abandon their cart
    predictions = model.predict_proba(X_sample)[:, 1]
    highest_abandon_idx = predictions.argmax()
    
    # Generate a waterfall plot for that specific prediction
    plt.figure()
    # For waterfall, we need an Explanation object
    explanation = shap.Explanation(
        values=shap_values[highest_abandon_idx], 
        base_values=explainer.expected_value, 
        data=X_sample.iloc[highest_abandon_idx].values,
        feature_names=X_sample.columns
    )
    shap.waterfall_plot(explanation, show=False)
    plt.tight_layout()
    plt.savefig('plots/shap_local_explanation.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    print("SHAP plots saved to the 'plots' directory.")

if __name__ == "__main__":
    run_shap_analysis()
