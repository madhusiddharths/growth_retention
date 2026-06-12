import pandas as pd
from google.cloud import bigquery
from scipy.stats import chi2_contingency

def run_ab_test():
    client = bigquery.Client()

    query = """
    SELECT 
        experiment_group,
        COUNT(user_id) as total_users,
        SUM(CASE WHEN total_purchases > 0 THEN 1 ELSE 0 END) as converted_users
    FROM `gen-lang-client-0874026413.cosmetics_gold.dim_users`
    GROUP BY 1
    """

    df = client.query(query).to_dataframe()
    
    print("--- A/B Test Results ---")
    print(df)
    
    # Extract values for contingency table
    control_converted = df[df['experiment_group'] == 0]['converted_users'].values[0]
    control_total = df[df['experiment_group'] == 0]['total_users'].values[0]
    
    treatment_converted = df[df['experiment_group'] == 1]['converted_users'].values[0]
    treatment_total = df[df['experiment_group'] == 1]['total_users'].values[0]
    
    control_not_converted = control_total - control_converted
    treatment_not_converted = treatment_total - treatment_converted
    
    # Contingency table: [[Control Converted, Control Not Converted], [Treatment Converted, Treatment Not Converted]]
    contingency_table = [
        [control_converted, control_not_converted],
        [treatment_converted, treatment_not_converted]
    ]
    
    chi2, p_value, dof, expected = chi2_contingency(contingency_table)
    
    print(f"\nChi-Square Statistic: {chi2:.4f}")
    print(f"P-Value: {p_value:.6e}")
    
    if p_value < 0.05:
        print("Result: STATISTICALLY SIGNIFICANT. The new checkout flow (Treatment) caused a measurable change in conversion rate.")
    else:
        print("Result: NOT STATISTICALLY SIGNIFICANT. We cannot conclude the new checkout flow had an impact.")

if __name__ == "__main__":
    run_ab_test()
