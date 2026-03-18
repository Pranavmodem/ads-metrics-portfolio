-- Business metrics mart: campaign-level KPIs
-- Computes CPM, CTR, ROAS, CPA, fill rate, and frequency
-- Source for reporting and analysis dashboards

WITH impressions AS (
    SELECT
        campaign_id,
        campaign_name,
        channel,
        DATE(event_timestamp) AS event_date,
        COUNT(DISTINCT impression_id) AS impressions,
        COUNT(DISTINCT user_id) AS unique_users,
        SUM(impression_cost) AS spend,
        SUM(CASE WHEN impression_cost = 0 THEN 1 ELSE 0 END) AS zero_cost_impressions,
    FROM {{ ref('stg_impressions') }}
    GROUP BY 1, 2, 3, 4
),

clicks AS (
    SELECT
        campaign_id,
        DATE(event_timestamp) AS event_date,
        COUNT(*) AS clicks,
        COUNT(DISTINCT user_id) AS users_who_clicked
    FROM {{ ref('events_clicks') }}
    GROUP BY 1, 2
),

conversions_agg AS (
    SELECT
        campaign_id,
        DATE(event_timestamp) AS event_date,
        COUNT(DISTINCT conversion_id) AS conversions,
        COUNT(DISTINCT user_id) AS users_who_converted,
        SUM(conversion_value_usd) AS revenue
    FROM {{ ref('stg_conversions') }}
    GROUP BY 1, 2
),

-- Join all metrics
campaign_metrics AS (
    SELECT
        i.campaign_id,
        i.campaign_name,
        i.channel,
        i.event_date,
        i.impressions,
        i.unique_users,
        i.spend,
        COALESCE(c.clicks, 0) AS clicks,
        COALESCE(c.users_who_clicked, 0) AS users_who_clicked,
        COALESCE(ca.conversions, 0) AS conversions,
        COALESCE(ca.users_who_converted, 0) AS users_who_converted,
        COALESCE(ca.revenue, 0) AS revenue,
        -- Computed metrics
        CASE
            WHEN i.spend > 0 THEN (i.spend / i.impressions) * 1000
            ELSE 0
        END AS cpm,
        CASE
            WHEN i.impressions > 0 THEN CAST(COALESCE(c.clicks, 0) AS FLOAT64) / i.impressions
            ELSE 0
        END AS ctr,
        CASE
            WHEN COALESCE(c.clicks, 0) > 0 THEN i.spend / COALESCE(c.clicks, 0)
            ELSE 0
        END AS cpc,
        CASE
            WHEN COALESCE(ca.conversions, 0) > 0 THEN i.spend / COALESCE(ca.conversions, 0)
            ELSE 0
        END AS cpa,
        CASE
            WHEN i.spend > 0 THEN COALESCE(ca.revenue, 0) / i.spend
            ELSE 0
        END AS roas,
        CASE
            WHEN COALESCE(c.clicks, 0) > 0 THEN CAST(COALESCE(ca.conversions, 0) AS FLOAT64) / COALESCE(c.clicks, 0)
            ELSE 0
        END AS cvr,
        CASE
            WHEN COALESCE(ca.conversions, 0) > 0 THEN COALESCE(ca.revenue, 0) / COALESCE(ca.conversions, 0)
            ELSE 0
        END AS aov,
        -- Fill rate: served impressions / potential impressions
        CASE
            WHEN (i.impressions + i.zero_cost_impressions) > 0
                THEN CAST(i.impressions AS FLOAT64) / (i.impressions + i.zero_cost_impressions)
            ELSE 1.0
        END AS fill_rate,
        -- Frequency: impressions per unique user
        CASE
            WHEN i.unique_users > 0 THEN CAST(i.impressions AS FLOAT64) / i.unique_users
            ELSE 0
        END AS frequency,
        CURRENT_TIMESTAMP() AS dbt_updated_at
    FROM impressions i
    LEFT JOIN clicks c
        ON i.campaign_id = c.campaign_id
        AND i.event_date = c.event_date
    LEFT JOIN conversions_agg ca
        ON i.campaign_id = ca.campaign_id
        AND i.event_date = ca.event_date
)

SELECT
    *
FROM campaign_metrics
ORDER BY event_date DESC, campaign_id
