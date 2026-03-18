# Ads Metrics Catalog

Comprehensive reference for all business metrics used in Netflix Ads analytics, including definitions, formulas, data sources, and usage guidelines.

## Overview

This catalog defines 20+ core metrics across five dimensions: efficiency, engagement, return, reach, and attribution. All metrics are calculated in the `mart_campaign_metrics` and `mart_attribution_summary` tables in BigQuery.

---

## Efficiency Metrics

### CPM (Cost Per Mille)

**Definition**: Average cost to reach 1,000 people with your ad

**Formula**: `(spend / impressions) * 1000`

**Data Source**: `mart_campaign_metrics`

**Dimensions**: Campaign, Channel, Date

**Business Owner**: Ads Finance

**Benchmark**: $2-$8 (channel and audience dependent)

**Calculation Frequency**: Daily

**Use Case**: Comparing inventory costs across channels and campaigns. Lower CPM generally indicates more efficient inventory.

**Notes**:
- Includes all paid impressions; excludes zero-cost impressions from our own network
- Can be anomalously low during periods of low demand

---

### CPC (Cost Per Click)

**Definition**: Average amount spent for each click on your ad

**Formula**: `spend / clicks`

**Data Source**: `mart_campaign_metrics`

**Dimensions**: Campaign, Channel, Date

**Business Owner**: Ads Finance

**Benchmark**: $0.50-$3.00 depending on channel

**Calculation Frequency**: Daily

**Use Case**: Evaluating the cost-efficiency of driving traffic. Compare CPC across campaigns to identify which channels drive clicks most efficiently.

**Notes**:
- Requires clicks data from ad server
- CPC = CPM * (1 / CTR)

---

### CPA (Cost Per Acquisition)

**Definition**: Average cost to acquire one paying customer

**Formula**: `spend / conversions`

**Data Source**: `mart_campaign_metrics`

**Dimensions**: Campaign, Channel, Date

**Business Owner**: Ads Finance

**Benchmark**: <= $50 (Netflix Premium tier)

**Calculation Frequency**: Daily

**Use Case**: Direct measure of acquisition efficiency. Critical for budget optimization and channel comparison.

**Notes**:
- Only includes paid conversions
- Does not account for lifetime value
- Can be volatile with low conversion volumes

---

## Engagement Metrics

### CTR (Click-Through Rate)

**Definition**: Percentage of impressions that result in a click

**Formula**: `(clicks / impressions) * 100`

**Data Source**: `mart_campaign_metrics`

**Dimensions**: Campaign, Channel, Date, Creative

**Business Owner**: Ads Analytics

**Benchmark**: >= 1.5% (Search), >= 0.5% (Display), >= 3% (Video)

**Calculation Frequency**: Daily

**Use Case**: Measuring creative performance and audience relevance. Higher CTR indicates better targeting or more compelling creatives.

**Notes**:
- Highly channel-dependent; benchmark varies significantly
- Can indicate creative fatigue if declining over time
- Formula: `CTR = CPC / CPM * 1000`

---

### CVR (Conversion Rate)

**Definition**: Percentage of clicks that result in conversions

**Formula**: `(conversions / clicks) * 100`

**Data Source**: `mart_campaign_metrics`

**Dimensions**: Campaign, Channel, Date

**Business Owner**: Ads Analytics

**Benchmark**: >= 3% (subscription), >= 2% (trial signup)

**Calculation Frequency**: Daily

**Use Case**: Measuring landing page effectiveness and post-click user experience.

**Notes**:
- Requires click and conversion tracking
- Highly dependent on landing page quality
- Mobile CVR typically lower than desktop

---

## ROI Metrics

### ROAS (Return On Ad Spend)

**Definition**: Revenue generated for every dollar spent on ads

**Formula**: `revenue / spend`

**Data Source**: `mart_campaign_metrics`

**Dimensions**: Campaign, Channel, Date

**Business Owner**: Ads Analytics

**Benchmark**: >= 4.0x (Netflix target)

**Calculation Frequency**: Daily

**Use Case**: Overall measure of campaign profitability. Primary metric for budget decisions.

**Notes**:
- This is the most important KPI for campaign optimization
- Accounts for both volume (CTR, CVR) and price (CPA)
- Sensitive to attribution model used; reported ROAS assumes last-touch

---

### AOV (Average Order Value)

**Definition**: Average revenue per conversion

**Formula**: `revenue / conversions`

**Data Source**: `mart_campaign_metrics`

**Dimensions**: Campaign, Channel, Date

**Business Owner**: Ads Analytics

**Benchmark**: $75-$150 (depends on subscription tier mix)

**Calculation Frequency**: Daily

**Use Case**: Understanding the quality of conversions. Higher AOV channels may justify higher CPA.

**Notes**:
- Denominator is conversion count, not customer count (repeat purchasers counted multiple times)
- Can vary significantly by device type and region

---

## Reach Metrics

### Impressions

**Definition**: Total number of ad impressions served

**Formula**: `COUNT(impression_id)`

**Data Source**: `staging_impressions`

**Dimensions**: Campaign, Channel, Date, Device Type

**Business Owner**: Ads Operations

**Calculation Frequency**: Daily

**Use Case**: Volume metric. Used to calculate CPM and assess inventory availability.

**Notes**:
- Includes all served impressions (both paid and earned)
- Excludes bot traffic and zero-cost impressions
- Late-arriving impressions may be backfilled up to 24 hours

---

### Unique Users

**Definition**: Number of distinct users reached by the campaign

**Formula**: `COUNT(DISTINCT user_id)`

**Data Source**: `staging_impressions`

**Dimensions**: Campaign, Channel, Date

**Business Owner**: Ads Analytics

**Calculation Frequency**: Daily

**Use Case**: Reach metric. Combined with frequency, indicates audience expansion vs. retention.

**Notes**:
- User identification based on cookie/device ID
- Subject to identity resolution errors (varies by 2-5%)

---

### Frequency

**Definition**: Average number of times an ad is shown to each unique user

**Formula**: `impressions / unique_users`

**Data Source**: `mart_campaign_metrics`

**Dimensions**: Campaign, Channel, Date

**Business Owner**: Ads Analytics

**Benchmark**: 3-7 (varies by campaign objective)

**Calculation Frequency**: Daily

**Use Case**: Understanding ad exposure. Higher frequency can improve conversion but risks ad fatigue.

**Notes**:
- Calculated as daily average; actual frequency distribution is multimodal
- Cross-campaign frequency not captured in this metric

---

### Fill Rate

**Definition**: Percentage of ad requests that result in served impressions

**Formula**: `served_impressions / (served_impressions + unfilled_requests) * 100`

**Data Source**: `mart_campaign_metrics`

**Dimensions**: Campaign, Channel, Date

**Business Owner**: Ads Operations

**Benchmark**: >= 95%

**Calculation Frequency**: Daily

**Use Case**: Inventory health monitoring. Low fill rate indicates supply constraints or demand mismatch.

**Notes**:
- Directly impacts volume and CPM
- Inversely related to CPM (low supply = higher prices)

---

## Attribution Metrics

### Attributed Revenue

**Definition**: Revenue attributed to a channel using multi-touch attribution model

**Formula**: `SUM(attribution_credit) by model`

**Data Source**: `mart_attribution_summary`

**Dimensions**: Channel, Attribution Model, Date

**Business Owner**: Ads Analytics

**Available Models**:
- **Last-Touch**: 100% credit to final channel interaction
- **First-Touch**: 100% credit to initial channel interaction
- **Linear**: Equal credit to all channels
- **Time-Decay**: Exponential decay (7-day half-life); recent interactions weighted higher

**Calculation Frequency**: Daily

**Attribution Window**: 28 days (configurable)

**Use Case**: Understanding true channel contribution in multi-touch journeys.

**Notes**:
- Assumes sequential user journey; cannot credit simultaneous touches
- Time-decay model recommended for most analyses
- Results should be compared across models to validate conclusions

---

## Key Metric Relationships

### Funnel Metrics (ordered by conversion stage)

```
Impressions → Clicks → Conversions → Revenue
     ↓            ↓          ↓           ↓
    CTR         CVR        AOV        ROAS
```

- CTR links impressions to clicks
- CVR links clicks to conversions
- AOV measures quality of conversions
- ROAS = CTR × CVR × AOV / CPA

### Cost Metrics (ordered by stage)

```
Spend / Impressions = CPM/1000
Spend / Clicks = CPC
Spend / Conversions = CPA
```

---

## Data Quality Rules

### Outlier Detection

| Metric | Min Value | Max Value |
|--------|-----------|-----------|
| CPM    | $0.10     | $100      |
| CTR    | 0.01%     | 50%       |
| CVR    | 0.1%      | 50%       |
| ROAS   | 0.1x      | 100x      |
| CPA    | $1        | $500      |

### Validation Rules

1. **Consistency Check**: ROAS should generally correlate with CTR and CVR
2. **Zero-Fill Validation**: Zero conversions + positive spend = valid (test campaign) or data quality issue
3. **Late Arrival Handling**: Conversions may arrive up to 72 hours after event; data stabilizes after 48 hours

---

## Seasonality Adjustments

The following months experience elevated performance due to seasonal demand:

| Month     | Adjustment Factor | Notes                           |
|-----------|-------------------|--------------------------------------|
| November  | 1.5x              | Black Friday / Holiday season prep   |
| December  | 2.0x              | Holiday season peak                  |
| January   | 1.2x              | New Year resolutions                 |
| May-July  | 0.9x              | Summer slowdown                      |

---

## Calculated Metric Hierarchy

Metrics are calculated in dependency order:

**Tier 1** (Source Counts): Impressions, Clicks, Conversions, Spend, Revenue

**Tier 2** (Basic Rates): CTR, CVR, CPM, CPC, Frequency, Fill Rate

**Tier 3** (Efficiency & Value): AOV, CPA, ROAS

**Tier 4** (Attribution): Attributed Revenue by Channel and Model

---

## Usage Guidelines

### For Campaign Optimization
Focus on: ROAS, CPA, CTR, and AOV

### For Budget Allocation
Use: ROAS, CPA, and projected volume (impressions × CTR × CVR)

### For Creative Testing
Monitor: CTR, CVR, and frequency

### For Channel Comparison
Use: ROAS, CPA, and attributed revenue (time-decay model)

### For Anomaly Detection
Watch: CTR trend, CPA trend, ROAS trend (should be relatively stable week-to-week)

---

## Questions & Support

- **Metric Definition Questions**: analytics@netflix.com
- **Data Discrepancies**: data-engineering@netflix.com
- **Dashboard Access Issues**: it-support@netflix.com
