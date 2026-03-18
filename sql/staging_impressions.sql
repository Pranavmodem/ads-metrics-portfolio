-- Staging model for raw impression events
-- Deduplicates, type-casts, and filters bot traffic
-- This follows dbt conventions for a staging layer

WITH raw_impressions AS (
    SELECT
        impression_id,
        user_id,
        campaign_id,
        campaign_name,
        channel,
        CAST(event_timestamp AS TIMESTAMP) AS event_timestamp,
        CAST(impression_cost AS FLOAT64) AS impression_cost,
        advertiser_id,
        creative_id,
        placement_id,
        device_type,
        country,
        is_bot AS raw_is_bot,
        _dbt_source_relation,
        _fivetran_synced,
        ROW_NUMBER() OVER (PARTITION BY impression_id ORDER BY _fivetran_synced DESC) AS rn
    FROM {{ ref('raw_impressions') }}
),

deduped AS (
    SELECT
        impression_id,
        user_id,
        campaign_id,
        campaign_name,
        channel,
        event_timestamp,
        impression_cost,
        advertiser_id,
        creative_id,
        placement_id,
        device_type,
        country,
        raw_is_bot,
        _dbt_source_relation,
        _fivetran_synced
    FROM raw_impressions
    WHERE rn = 1  -- Keep only latest version of each impression
),

filtered AS (
    SELECT
        impression_id,
        user_id,
        campaign_id,
        campaign_name,
        channel,
        event_timestamp,
        impression_cost,
        advertiser_id,
        creative_id,
        placement_id,
        device_type,
        country,
        -- Flag obvious bot traffic
        raw_is_bot OR (impression_cost = 0 AND event_timestamp IS NOT NULL) AS is_bot_flag,
        -- Generate surrogate key
        GENERATE_UUID() AS impression_key,
        CURRENT_TIMESTAMP() AS dbt_updated_at
    FROM deduped
    WHERE
        -- Remove impressions with missing critical fields
        impression_id IS NOT NULL
        AND user_id IS NOT NULL
        AND campaign_id IS NOT NULL
        AND event_timestamp IS NOT NULL
        AND event_timestamp >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)  -- Last 90 days
)

SELECT
    *
FROM filtered
WHERE NOT is_bot_flag  -- Final filter to exclude bots
