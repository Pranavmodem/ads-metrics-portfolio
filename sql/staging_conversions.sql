-- Staging model for raw conversion events
-- Handles late-arrival conversions, deduplication, and type-casting
-- Follows dbt conventions

WITH raw_conversions AS (
    SELECT
        conversion_id,
        user_id,
        campaign_id,
        order_id,
        CAST(event_timestamp AS TIMESTAMP) AS event_timestamp,
        CAST(conversion_value AS FLOAT64) AS conversion_value,
        CAST(conversion_value_usd AS FLOAT64) AS conversion_value_usd,
        conversion_type,
        advertiser_id,
        country,
        device_type,
        _dbt_source_relation,
        _fivetran_synced,
        -- Handle late arrivals (conversions can arrive up to 72 hours after event)
        ROW_NUMBER() OVER (PARTITION BY conversion_id ORDER BY _fivetran_synced DESC) AS rn
    FROM {{ ref('raw_conversions') }}
),

deduped AS (
    SELECT
        conversion_id,
        user_id,
        campaign_id,
        order_id,
        event_timestamp,
        conversion_value,
        conversion_value_usd,
        conversion_type,
        advertiser_id,
        country,
        device_type,
        _dbt_source_relation,
        _fivetran_synced
    FROM raw_conversions
    WHERE rn = 1  -- Keep only latest version of each conversion
),

validated AS (
    SELECT
        conversion_id,
        user_id,
        campaign_id,
        order_id,
        event_timestamp,
        -- Use local currency value, fallback to USD
        COALESCE(conversion_value, conversion_value_usd, 0) AS conversion_value,
        conversion_value_usd,
        conversion_type,
        advertiser_id,
        country,
        device_type,
        -- Flag data quality issues
        CASE
            WHEN conversion_value IS NULL AND conversion_value_usd IS NULL THEN TRUE
            WHEN event_timestamp IS NULL THEN TRUE
            WHEN user_id IS NULL THEN TRUE
            ELSE FALSE
        END AS is_invalid_record,
        -- Surrogates and audit
        GENERATE_UUID() AS conversion_key,
        CASE
            WHEN _fivetran_synced > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 72 HOUR)
                THEN TRUE
            ELSE FALSE
        END AS is_late_arrival,
        CURRENT_TIMESTAMP() AS dbt_updated_at
    FROM deduped
)

SELECT
    *
FROM validated
WHERE
    -- Filter invalid records
    NOT is_invalid_record
    -- Only include conversions from last 90 days
    AND event_timestamp >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    AND event_timestamp <= CURRENT_TIMESTAMP()
