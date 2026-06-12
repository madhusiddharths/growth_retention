{{ config(materialized='table') }}

WITH sessions AS (
    SELECT * FROM {{ ref('fact_user_sessions') }}
),

user_agg AS (
    SELECT 
        user_id,
        MAX(experiment_group) AS experiment_group,
        MIN(session_start) AS first_seen,
        MAX(session_start) AS last_seen,
        COUNT(global_session_id) AS total_sessions,
        SUM(total_views) AS total_views,
        SUM(total_carts) AS total_carts,
        SUM(total_purchases) AS total_purchases,
        SUM(session_revenue) AS lifetime_value,
        TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(session_start), DAY) AS days_since_last_session
    FROM sessions
    GROUP BY 1
)

SELECT * FROM user_agg
