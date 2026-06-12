{{ config(materialized='view') }}

WITH raw_events AS (
    SELECT * FROM `gen-lang-client-0874026413.cosmetics_bronze.events`
)

SELECT
    CAST(event_time AS TIMESTAMP) AS event_time,
    CAST(event_type AS STRING) AS event_type,
    CAST(product_id AS INT64) AS product_id,
    CAST(category_id AS INT64) AS category_id,
    CAST(category_code AS STRING) AS category_code,
    CAST(brand AS STRING) AS brand,
    CAST(price AS FLOAT64) AS price,
    CAST(user_id AS STRING) AS user_id,
    CAST(user_session AS STRING) AS user_session,
    CAST(experiment_group AS INT64) AS experiment_group
FROM raw_events
WHERE user_id IS NOT NULL AND CAST(user_id AS STRING) != 'unknown' AND user_session IS NOT NULL
