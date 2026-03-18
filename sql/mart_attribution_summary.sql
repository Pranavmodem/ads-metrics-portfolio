-- Attribution results aggregated by campaign, channel, and model
-- Summarizes multi-touch attribution analysis results
-- Used for measuring true contribution of each channel

WITH conversions_with_touches AS (
    SELECT
        c.conversion_id,
        c.user_id,
        c.campaign_id,
        c.event_timestamp AS conversion_timestamp,
        c.conversion_value_usd,
        -- Get all impressions for this user in the last N days (attribution window)
        ARRAY_AGG(
            STRUCT(
                i.campaign_id,
                i.channel,
                i.event_timestamp,
                i.impression_cost
            )
            ORDER BY i.event_timestamp ASC
        ) AS impression_journey
    FROM {{ ref('stg_conversions') }} c
    LEFT JOIN {{ ref('stg_impressions') }} i
        ON c.user_id = i.user_id
        AND i.event_timestamp <= c.event_timestamp
        -- Attribution window: last 28 days (configurable)
        AND i.event_timestamp >= TIMESTAMP_SUB(c.event_timestamp, INTERVAL 28 DAY)
    GROUP BY 1, 2, 3, 4, 5
),

attribution_last_touch AS (
    -- Last-touch attribution: credit to final channel
    SELECT
        c.conversion_id,
        c.user_id,
        c.campaign_id,
        c.conversion_timestamp,
        c.conversion_value_usd,
        'last_touch' AS attribution_model,
        (
            SELECT touch.channel
            FROM UNNEST(c.impression_journey) AS touch
            ORDER BY touch.event_timestamp DESC
            LIMIT 1
        ) AS credited_channel,
        (
            SELECT touch.campaign_id
            FROM UNNEST(c.impression_journey) AS touch
            ORDER BY touch.event_timestamp DESC
            LIMIT 1
        ) AS credited_campaign,
        c.conversion_value_usd AS attributed_revenue,
        1 AS touch_count
    FROM conversions_with_touches c
    WHERE ARRAY_LENGTH(c.impression_journey) > 0
),

attribution_first_touch AS (
    -- First-touch attribution: credit to initial channel
    SELECT
        c.conversion_id,
        c.user_id,
        c.campaign_id,
        c.conversion_timestamp,
        c.conversion_value_usd,
        'first_touch' AS attribution_model,
        (
            SELECT touch.channel
            FROM UNNEST(c.impression_journey) AS touch
            ORDER BY touch.event_timestamp ASC
            LIMIT 1
        ) AS credited_channel,
        (
            SELECT touch.campaign_id
            FROM UNNEST(c.impression_journey) AS touch
            ORDER BY touch.event_timestamp ASC
            LIMIT 1
        ) AS credited_campaign,
        c.conversion_value_usd AS attributed_revenue,
        1 AS touch_count
    FROM conversions_with_touches c
    WHERE ARRAY_LENGTH(c.impression_journey) > 0
),

-- Union all models
all_attributions AS (
    SELECT * FROM attribution_last_touch
    UNION ALL
    SELECT * FROM attribution_first_touch
),

-- Aggregate by campaign, channel, and model
attribution_summary AS (
    SELECT
        attribution_model,
        credited_channel,
        credited_campaign,
        COUNT(DISTINCT conversion_id) AS attributed_conversions,
        COUNT(DISTINCT user_id) AS attributed_users,
        SUM(attributed_revenue) AS attributed_revenue,
        AVG(attributed_revenue) AS avg_order_value,
        PERCENTILE_CONT(attributed_revenue, 0.5) OVER (
            PARTITION BY attribution_model, credited_channel, credited_campaign
        ) AS median_order_value,
        CURRENT_TIMESTAMP() AS dbt_updated_at
    FROM all_attributions
    GROUP BY 1, 2, 3
)

SELECT
    *
FROM attribution_summary
ORDER BY attribution_model, attributed_revenue DESC
