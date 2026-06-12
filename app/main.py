import streamlit as st
import requests
import base64
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery

st.set_page_config(page_title="Cart Abandonment Predictor", layout="wide")

st.title("🛒 E-Commerce Growth & Retention Platform")

tab1, tab2, tab3 = st.tabs(["🔮 Real-Time Predictor", "📊 Live A/B Test Dashboard", "📂 Bulk Prediction"])

with tab1:
    st.markdown("### Predict real-time cart abandonment using XGBoost & SHAP")
    
    st.sidebar.header("Real-Time Predictor Settings")
    total_views = st.sidebar.slider("Total Product Views", min_value=1, max_value=50, value=5)
    total_carts = st.sidebar.slider("Items Added to Cart", min_value=1, max_value=50, value=2)
    session_duration = st.sidebar.slider("Session Duration (minutes)", min_value=1, max_value=120, value=15)
    experiment_group = st.sidebar.selectbox("Checkout Experience", options=["Old (Control)", "New (Treatment)"])

    exp_val = 1 if "New" in experiment_group else 0

    if st.button("Predict Abandonment", type="primary"):
        payload = {
            "total_views": float(total_views),
            "total_carts": float(total_carts),
            "session_duration_minutes": float(session_duration),
            "experiment_group": float(exp_val)
        }
        
        with st.spinner("Analyzing session..."):
            try:
                api_url = os.getenv("API_URL", "http://api:8000/predict")
                response = requests.post(api_url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    prob = data["abandonment_probability"]
                    img_b64 = data["shap_plot_b64"]
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.subheader("Prediction Result")
                        if prob > 0.5:
                            st.error(f"High Risk of Abandonment: **{prob*100:.1f}%**")
                        else:
                            st.success(f"Low Risk of Abandonment: **{prob*100:.1f}%**")
                            
                        st.progress(prob)
                        
                        st.info("💡 **Tip**: To simulate a purchase (low abandonment risk), increase the number of items added to cart (e.g., 20) and use the New Checkout experience.")
                    
                    with col2:
                        st.subheader("SHAP Explanation")
                        st.markdown("See exactly how each feature contributed to the final probability.")
                        img_bytes = base64.b64decode(img_b64)
                        st.image(img_bytes, use_container_width=True)
                else:
                    st.error("Error from API backend.")
            except Exception as e:
                st.error(f"Failed to connect to API. Ensure the backend is running. {e}")

with tab2:
    st.markdown("### Live A/B Test Dashboard (BigQuery)")
    st.markdown("Pulling live aggregated session data from the Modern Data Stack.")
    
    if st.button("Load Dashboard Data"):
        with st.spinner("Querying BigQuery..."):
            try:
                project = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0874026413")
                client = bigquery.Client(project=project)
                # Query funnel metrics
                query = """
                SELECT 
                    experiment_group,
                    COUNT(user_id) as total_users,
                    SUM(CASE WHEN total_carts > 0 THEN 1 ELSE 0 END) as users_with_carts,
                    SUM(CASE WHEN total_purchases > 0 THEN 1 ELSE 0 END) as converted_users,
                    SUM(lifetime_value) as total_revenue
                FROM `gen-lang-client-0874026413.cosmetics_gold.dim_users`
                GROUP BY 1
                ORDER BY 1
                """
                df = client.query(query).to_dataframe()
                
                df['group_name'] = df['experiment_group'].map({0: 'Control (Old)', 1: 'Treatment (New)'})
                df['conversion_rate'] = (df['converted_users'] / df['total_users']) * 100
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                control_rev = df[df['experiment_group'] == 0]['total_revenue'].values[0]
                treatment_rev = df[df['experiment_group'] == 1]['total_revenue'].values[0]
                
                control_cr = df[df['experiment_group'] == 0]['conversion_rate'].values[0]
                treatment_cr = df[df['experiment_group'] == 1]['conversion_rate'].values[0]
                
                col1.metric("Control Revenue", f"${control_rev:,.2f}")
                col2.metric("Treatment Revenue", f"${treatment_rev:,.2f}", f"{((treatment_rev/control_rev)-1)*100:.1f}%")
                col3.metric("Treatment Conv. Rate", f"{treatment_cr:.2f}%", f"{treatment_cr - control_cr:.2f}%")
                
                st.divider()
                
                # Funnel Chart using Plotly
                fig = go.Figure()
                
                for _, row in df.iterrows():
                    fig.add_trace(go.Funnel(
                        name = row['group_name'],
                        y = ["Total Users", "Users With Carts", "Converted Users"],
                        x = [row['total_users'], row['users_with_carts'], row['converted_users']],
                        textinfo = "value+percent initial"
                    ))
                
                fig.update_layout(title="Conversion Funnel: Control vs Treatment")
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Failed to query BigQuery: {e}")

with tab3:
    st.markdown("### Bulk Prediction")
    st.markdown("Upload a CSV file containing user sessions to score them in bulk.")
    
    st.info("The CSV must contain the following columns: `total_views`, `total_carts`, `session_duration_minutes`, `experiment_group`")
    
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    
    if uploaded_file is not None:
        bulk_df = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded data:")
        st.dataframe(bulk_df.head())
        
        if st.button("Run Bulk Prediction"):
            try:
                # Prepare payload
                sessions = bulk_df[['total_views', 'total_carts', 'session_duration_minutes', 'experiment_group']].to_dict(orient='records')
                payload = {"sessions": sessions}
                
                with st.spinner("Scoring sessions..."):
                    api_url = os.getenv("API_URL", "http://api:8000")
                    response = requests.post(f"{api_url.replace('/predict', '')}/bulk_predict", json=payload)
                    
                    if response.status_code == 200:
                        predictions = response.json()["predictions"]
                        bulk_df["abandonment_probability"] = predictions
                        bulk_df["predicted_class"] = bulk_df["abandonment_probability"].apply(lambda x: "Abandon" if x > 0.5 else "Purchase")
                        
                        st.success("Scoring complete!")
                        st.dataframe(bulk_df.head(10))
                        
                        csv = bulk_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Download Scored CSV",
                            data=csv,
                            file_name='scored_sessions.csv',
                            mime='text/csv',
                        )
                    else:
                        st.error("Error from API backend.")
            except Exception as e:
                st.error(f"Bulk prediction failed: {e}")
