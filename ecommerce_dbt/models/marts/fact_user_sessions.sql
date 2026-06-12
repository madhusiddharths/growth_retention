{{ config(materialized='table') }}

WITH events AS (
    SELECT * FROM {{ ref('stg_events') }}
),

-- Sort events and calculate time difference to the previous event for the same user
lagged_events AS (
    SELECT 
        *,
        LAG(event_time) OVER (PARTITION BY user_id ORDER BY event_time ASC) as prev_event_time
    FROM events
),

-- If the difference is > 30 mins, or it's the first event, mark as a new session (1)
new_session_flag AS (
    SELECT 
        *,
        CASE 
            WHEN prev_event_time IS NULL THEN 1
            WHEN TIMESTAMP_DIFF(event_time, prev_event_time, MINUTE) > 30 THEN 1
            ELSE 0 
        END as is_new_session
    FROM lagged_events
),

-- Cumulative sum of the new session flag generates a unique session ID for the user
session_ids AS (
    SELECT 
        *,
        SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY event_time ASC) as user_session_seq
    FROM new_session_flag
),

-- Aggregate to the session level
session_agg AS (
    SELECT
        user_id,
        user_session_seq,
        CONCAT(user_id, '-', CAST(user_session_seq AS STRING)) AS global_session_id,
        MIN(event_time) AS session_start,
        MAX(event_time) AS session_end,
        COUNT(event_time) AS total_events,
        SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) AS total_views,
        SUM(CASE WHEN event_type = 'cart' THEN 1 ELSE 0 END) AS total_carts,
        SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS total_purchases,
        SUM(CASE WHEN event_type = 'purchase' THEN price ELSE 0 END) AS session_revenue,
        MAX(experiment_group) AS experiment_group
    FROM session_ids
    GROUP BY 1, 2, 3
)

SELECT * FROM session_agg
