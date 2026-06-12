import pandas as pd
import numpy as np
import os
from evidently import Report
from evidently.presets import DataDriftPreset

def generate_report():
    print("Loading reference data...")
    reference_data = pd.read_csv('models/X_train_sample.csv')
    
    print("Simulating current production data (with drift)...")
    current_data = reference_data.copy()
    current_data['total_carts'] = current_data['total_carts'] * np.random.uniform(1, 2.5, len(current_data))
    current_data['session_duration_minutes'] = current_data['session_duration_minutes'] * np.random.uniform(0.5, 3.0, len(current_data))
    
    print("Generating Evidently Data Drift Report...")
    report = Report(metrics=[
        DataDriftPreset(),
    ])
    
    report.run(reference_data=reference_data, current_data=current_data)
    
    # Save the report
    report.save_html('drift_report.html')
    print("Report saved as observability/drift_report.html")

if __name__ == "__main__":
    generate_report()
