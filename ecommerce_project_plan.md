# E-Commerce Growth & Retention: The Checkout Experiment
**Project Analysis & Phase-by-Phase Blueprint**

## Executive Analysis
This project plan is exceptionally strong. By bridging Data Engineering, Analytics Engineering, Statistical Analysis, and Machine Learning, it effectively targets the "Full-Stack Data Scientist" or "Machine Learning Engineer" archetype. 

It tells a compelling business story (reducing cart abandonment and proving revenue lift via A/B testing) while utilizing a highly relevant "Modern Data Stack" (MDS) and MLOps toolchain. This prevents the project from looking like a standard, sterile Kaggle exercise and elevates it to an enterprise-grade portfolio piece.

Below is the detailed, phase-by-phase breakdown of how data flows through the system, what is produced at each step, and how each phase enables the next.

---

## Phase 1: Data Sourcing, Engineering & Storage
**Goal:** Ingest raw clickstream data, simulate a realistic business experiment, and land the data securely in a cloud data lake/warehouse.

*   **Inputs:** 
    *   Raw CSV files from the Kaggle "eCommerce Events History in Cosmetics Shop" dataset.
*   **Process:**
    1.  **Experiment Simulation (Python):** Write a Python script to ingest the raw CSVs. Hash the `user_id` to randomly and deterministically assign users to either a `Control` (old checkout) or `Treatment` (new checkout) group. 
    2.  **Data Manipulation:** Artificially inject a conversion uplift for the `Treatment` group by converting a percentage of `cart` events into `purchase` events. Add an `experiment_group` column.
    3.  **Data Lake (GCS):** Upload the modified dataset to Google Cloud Storage (GCS) as partitioned raw files.
    4.  **Data Warehouse (BigQuery):** Create external tables or use BigQuery Data Transfer to load the GCS data into a BigQuery `Bronze` (raw) dataset.
*   **Outputs:** 
    *   `Bronze` dataset in BigQuery containing millions of rows of raw, uncleaned event logs, complete with A/B test assignments.
*   **Transition to Phase 2:** This raw `Bronze` data serves as the foundational source for your dbt transformation pipeline.

---

## Phase 2: Processing, Transformation & Testing (Modern Data Stack)
**Goal:** Clean, model, and aggregate the raw data into business-ready tables using software engineering best practices.

*   **Inputs:** BigQuery `Bronze` tables.
*   **Mandatory Tools:** `dbt`, `SQL`, `Great Expectations` (or dbt tests).
*   **Process:**
    1.  **Data Observability:** Implement `Great Expectations` or `dbt tests` on the incoming data to assert data quality (e.g., `user_id` is not null, `event_type` is within accepted values, timestamps are valid).
    2.  **Staging (Silver Layer):** Write dbt models to cast data types, handle timezones, extract date parts, and filter out malformed records.
    3.  **Marts (Gold Layer):** Write advanced SQL utilizing **CTEs** and **Window Functions**.
        *   `fact_user_sessions`: Use `LAG()`, `LEAD()`, and `ROW_NUMBER()` to group individual click events into logical sessions based on a 30-minute inactivity timeout window.
        *   `dim_users`: Calculate user lifetime value (LTV), total sessions, days since last purchase, and store their `experiment_group`.
*   **Outputs:** 
    *   A documented dbt project.
    *   Cleaned, structured `Gold` tables (`fact_user_sessions`, `dim_users`, `fact_events`) residing in BigQuery.
*   **Transition to Phase 3 & 4:** These `Gold` tables act as the Single Source of Truth (SSOT). They provide the analytical data for BI Dashboards (Phase 4) and the training features for the ML model (Phase 3).

---

## Phase 3: Statistical Analysis & Machine Learning
**Goal:** Statistically validate the A/B test and train an interpretable machine learning model to predict cart abandonment.

*   **Inputs:** BigQuery `Gold` tables.
*   **Mandatory Tools:** `Python (SciPy/Statsmodels)`, `XGBoost/LightGBM`, `SHAP`.
*   **Process:**
    1.  **A/B Testing (Statsmodels/SciPy):** Pull session and conversion data into a Jupyter Notebook. Run two-sample t-tests or Chi-Square tests to evaluate the conversion rate and Revenue Per Visitor (RPV) differences between the Control and Treatment groups. Calculate p-values and confidence intervals to prove the new checkout's efficacy.
    2.  **Feature Engineering:** Extract features from the Gold tables, such as `session_duration`, `items_in_cart`, `category_viewed`, and `historical_abandonment_rate`.
    3.  **Model Training:** Train an `XGBoost` or `LightGBM` binary classifier to predict whether a user with items in their cart will abandon it within the hour.
    4.  **Explainability (SHAP):** Compute SHAP values for the model. Generate a **SHAP Summary Plot** to show global feature importance and a **SHAP Force Plot** for individual prediction explanations.
*   **Outputs:** 
    *   A serialized, trained ML model file (e.g., `.pkl` or `.joblib`).
    *   Saved SHAP explainer objects.
    *   A Jupyter Notebook detailing the statistical proof of the A/B test.
*   **Transition to Phase 4:** The statistical findings provide the narrative for the BI dashboard. The serialized model and SHAP explainers are packaged for the web application deployment.

---

## Phase 4: Deployment & Observability
**Goal:** Serve the BI insights to stakeholders and deploy the ML model as an interactive, monitored web application.

*   **Inputs:** Serialized ML Model, SHAP explainers, BigQuery Gold tables.
*   **Mandatory Tools:** `Tableau or Power BI`, `FastAPI`, `Streamlit`, `Docker`, `Google Cloud Run`, `Evidently AI`.
*   **Process:**
    1.  **BI Deployment (Tableau/Power BI):** Connect directly to the BigQuery Gold tables. Build a dashboard visualizing the A/B test results (conversion lift, revenue impact) and the overall purchase funnel drop-offs. Publish it to the web.
    2.  **API Backend (FastAPI):** Build a REST API with an endpoint (`/predict`). It accepts user session parameters, passes them through the loaded XGBoost model, and returns the probability of abandonment along with SHAP values.
    3.  **Frontend Application (Streamlit):** Build a UI where users can tweak session parameters (e.g., "What if the user spends 45 minutes on the site?"). The app calls the FastAPI backend and visualizes the returned probability and the SHAP Force Plot.
    4.  **Containerization & Hosting (Docker & Cloud Run):** Write `Dockerfile`s for both FastAPI and Streamlit. Build the images and deploy them to `Google Cloud Run` for scalable, serverless hosting.
    5.  **Model Observability (Evidently AI):** Integrate Evidently AI to monitor the inputs hitting the FastAPI endpoint. Generate reports to track **Data Drift** (e.g., detecting if the distribution of incoming session lengths deviates significantly from the data the model was trained on).
*   **Outputs:** 
    *   A live, interactive Tableau/Power BI Dashboard.
    *   A public-facing Web App (Streamlit frontend + FastAPI backend) hosted on Cloud Run.
    *   Automated model health and data drift reports via Evidently AI.

---

## Phase 5: Polish & Expansion (Next Steps)
**Goal:** Elevate the MVP into a highly robust, automated, and feature-rich enterprise application.

*   **Inputs:** Existing Data Pipeline, ML Model, and Web App.
*   **Mandatory Tools:** `Apache Airflow`, `Plotly`, `Advanced SQL`.
*   **Process:**
    1.  **Dashboard Upgrade (Streamlit + Plotly):** Transform the Streamlit app into a multi-tab application. 
        *   Add an **A/B Test Live Dashboard** tab connecting directly to BigQuery to visualize funnel metrics.
        *   Add a **Bulk Prediction** tab allowing CSV uploads of session data for batch scoring.
        *   Replace static Matplotlib charts with interactive JavaScript Plotly charts.
    2.  **Advanced Feature Engineering:** Return to the dbt Gold layer to calculate richer predictive signals:
        *   **Temporal Features:** `day_of_week`, `hour_of_day`, `is_weekend`.
        *   **User History:** Calculate `historical_abandonment_rate` and `days_since_last_purchase` by joining `dim_users` into `fact_user_sessions`.
    3.  **Pipeline Orchestration (Apache Airflow):** Write Directed Acyclic Graphs (DAGs) to automate the manual workflow. The DAG should sense new data in GCS, trigger the BigQuery load, run `dbt build`, and automatically trigger a model retraining job.
*   **Outputs:** 
    *   A multi-tab, highly interactive Streamlit application.
    *   A fully automated orchestration pipeline using Airflow.

---

## Summary of the Final Deliverable
By the end of Phase 5, you will have a comprehensive portfolio piece that demonstrates:
1. You can handle raw data and design enterprise-grade data models (dbt, BigQuery).
2. You understand business metrics and rigorous statistical testing (SciPy, A/B Testing).
3. You can build and explain predictive models (XGBoost, SHAP).
4. You know how to put models into production and monitor them (FastAPI, Docker, GCP, Evidently AI).
5. You can automate and orchestrate complex DAGs (Apache Airflow) and deliver polished BI Dashboards.
