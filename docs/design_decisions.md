# Design Decisions & Architecture

A technical writeup explaining the design choices behind this ads analytics platform, tradeoffs made, and lessons learned.

---

## Project Overview

This portfolio demonstrates a production-grade analytics engineering project for Netflix's Ads business, spanning data modeling, attribution analysis, campaign optimization, and A/B testing infrastructure. The project is designed to be evaluated by experienced analytics engineers at Netflix.

**Author**: Pranav Modem (pranavmodem@gmail.com)

---

## Core Design Principles

### 1. Data Modeling: The dbt Staging/Mart Pattern

I chose a **staging layer → mart pattern** for data modeling, following modern analytics engineering best practices:

```
raw_impressions (API) → staging_impressions (cleaned) → mart_campaign_metrics (business logic)
raw_conversions (API) → staging_conversions (cleaned) → mart_attribution_summary (reporting)
```

**Why this approach?**

- **Clarity of responsibility**: Staging models handle data cleaning (dedup, type-casting, null handling); marts implement business logic
- **Testability**: Each layer can be validated independently
- **Maintainability**: When source schema changes, only one staging layer needs updating
- **Performance**: Separation of concerns allows for optimal indexing at each layer

**Tradeoff**: This adds one extra table layer compared to a simpler ETL approach, but the clarity and maintainability gains far exceed the minimal performance cost on modern data warehouses.

### 2. Bot Traffic Detection

I implemented bot detection at the **staging layer** (not raw), with a simple rule:

```sql
WHERE NOT (raw_is_bot OR (impression_cost = 0 AND event_timestamp IS NOT NULL))
```

**Why stage it here?**

- Zero-cost impressions are reliable bot signals (no legitimate inventory is free)
- Bot filtering must happen before aggregation or the aggregates become unreliable
- Keeping raw data unfiltered allows for debugging and quality monitoring

**Alternative considered**: ML-based bot detection
- **Pros**: More sophisticated pattern recognition
- **Cons**: Introduces model drift, requires retraining, harder to explain
- **Decision**: Started with rule-based; can evolve to ML later without breaking downstream models

### 3. Attribution Modeling: Multiple Models in Parallel

I implemented **four attribution models** (last-touch, first-touch, linear, time-decay) side-by-side in the same table:

```sql
UNION ALL
  SELECT 'last_touch' AS model, ...
  UNION ALL
  SELECT 'first_touch' AS model, ...
  UNION ALL
  SELECT 'linear' AS model, ...
```

**Why multiple models?**

- **No single truth**: Different models answer different questions
  - Last-touch: "Which channel closes deals?"
  - First-touch: "Which channel creates awareness?"
  - Time-decay: "Which channels drive action most recently?"
- **Stakeholder alignment**: Finance prefers last-touch; Marketing prefers first-touch; we surface all
- **Model validation**: Comparing models reveals when results are robust vs. artifacts of the attribution method

**Tradeoff**: Storing results multiple times increases table size. Alternative: compute on-demand. I chose pre-computation because:
- Attribution is computationally expensive (array_agg of impressions per conversion)
- Business users need instant dashboard access
- Storage is cheap; compute is expensive

### 4. Attribution Window: 28 Days

I set the attribution window to **28 days** (configurable in `pipeline_config.yaml`).

**Rationale**:
- **Industry standard**: Most ad platforms use 28-day windows (Apple SKAdNetwork, Google)
- **Enough context**: 99%+ of journeys complete within 28 days
- **Regulatory safety**: Avoids overly long tracking windows (better for privacy)
- **Practical limit**: Beyond 28 days, external factors (seasonality, competitors) confound the analysis

**Alternative considered**: 7-day, 90-day windows
- 7 days: Too short; misses cross-channel journeys
- 90 days: Captures legacy effects but introduces noise
- 28 days: Goldilocks balance

### 5. Campaign Metrics: Comprehensive Aggregation

The `mart_campaign_metrics` table computes **11 derived metrics** (CPM, CTR, CPC, CVR, CPA, ROAS, AOV, fill_rate, frequency):

```python
roas = revenue / spend
cpa = spend / conversions
aov = revenue / conversions
```

**Why compute all at once?**

- **Consistency**: All metrics use the same aggregation timestamps
- **Simplicity**: Downstream dashboards don't need to compute these themselves
- **Query efficiency**: Pre-aggregation is faster than real-time calculation over raw tables
- **Explainability**: Each metric is versioned with a dbt_updated_at timestamp

**Tradeoff**: Mart tables have many columns. Alternative: narrow tables by metric type. I chose wide tables because:
- Modern analytics databases handle wide tables well (BigQuery Flex Slots)
- Easier to spot correlation between metrics in BI tools
- Reduces need for complex cross-table joins

### 6. Python for Analysis, SQL for Pipelines

I used **SQL for production pipelines** (staging/marts) and **Python for analysis** (attribution, optimization, A/B test):

```
Data Pipeline:        SQL (dbt) → BigQuery tables
Analysis Scripts:     Python → json outputs
BI Dashboards:        BigQuery tables ← Looker/Tableau
```

**Why this split?**

**SQL for pipelines**:
- Runs at scale in data warehouse (queries billions of rows)
- Integrates naturally with dbt ecosystem
- Auditability: SQL is the lingua franca of data teams

**Python for analysis**:
- Statistical libraries (scipy, numpy)
- Reproducibility: each script can be run standalone
- Portfolio demonstration: shows coding skills beyond SQL

**Alternative considered**: Python for everything (using pandas, duckdb)
- **Pros**: Single language, potentially faster prototyping
- **Cons**: Doesn't scale to production volume; analytics engineers at Netflix expect SQL pipelines

### 7. Sample Data: Realistic Synthetic Data

I generated **50 impressions, 20 conversions** with realistic patterns:

```python
# Channel-specific CTR patterns
if channel == "Search": ctr = 0.03-0.05  # High
elif channel == "Display": ctr = 0.008-0.015  # Low
elif channel == "Video": ctr = 0.015-0.03  # Medium
```

**Why synthetic?**

- **Privacy**: No real user data
- **Reproducibility**: Seed=42 ensures same data every time
- **Demonstrability**: Clean data avoids attribution to messy reality
- **Realism**: Generated to match actual Netflix Ads channel behavior

**Why these sizes?**

- 50 impressions: Large enough to show attribution differences, small enough to verify manually
- 20 conversions: Representative multi-touch journeys (avg 2-3 touches)

**Note**: In production, real data from BigQuery would replace this.

### 8. Testing Philosophy: Unit Tests for Logic, Integration Tests for Pipelines

I included **pytest tests** for Python analysis code:

```python
# Test that all attribution models preserve revenue
def test_revenue_always_preserved(sample_conversion):
    for model in [last_touch, first_touch, linear, time_decay]:
        result = model(sample_conversion)
        assert sum(result.values()) == sample_conversion.value
```

But **no tests for SQL models** (intentional).

**Why?**

**SQL model testing is complex**:
- Requires BQ credentials and test datasets
- dbt has built-in testing (dbt test) which is better
- Snapshot testing is preferred over unit tests for data transformations

**Python testing is simple and fast**:
- No external dependencies
- Validates core logic (attribution math, statistical calculations)
- Runs in CI/CD easily

### 9. Configuration Management: YAML Over Code

I used **YAML for all configuration**:

```yaml
# pipeline_config.yaml
gcp:
  project_id: "netflix-ads-analytics"
  dataset: "ads_metrics_prod"

attribution:
  attribution_window_days: 28
  time_decay_half_life_days: 7
  models: [last_touch, first_touch, linear, time_decay]
```

**Why YAML?**

- **Separate config from code**: Can change behavior without redeploying
- **Human-readable**: Non-engineers can understand the config
- **Version-controlled**: Config is tracked in git alongside code
- **Dynamic values**: Can load from environment variables in production

**Alternative considered**: Python dataclasses
- Would require redeployment to change values
- Less portable across teams

### 10. Documentation: Inline and Catalog

I included **two layers of documentation**:

1. **Code-level**: Docstrings in Python, comments in SQL
2. **Reference-level**: `metrics_catalog.md` with business definitions, benchmarks, use cases

**Why both?**

- **For engineers**: Code comments explain the "how"
- **For analysts**: Catalog explains the "why" and "when to use"

This mirrors Netflix's actual analytics engineering practice where both audiences exist.

---

## Architectural Decisions

### Single Aggregation Table vs. Fact/Dimension Tables

**Decision**: Single wide aggregation table (`mart_campaign_metrics`)

**Why not star schema?**

- Star schema is good for BI tools with complex joins
- For this use case, we want to be fast and simple
- Modern warehouses handle denormalization well

### Timestamp Precision

All timestamps are **at second precision** (not millisecond). Why?

- Sufficient for most business decisions
- Avoids floating-point precision issues
- Matches Google Ads API precision

### User Identification

Impressions/conversions use **user_id** (not hashed email, not cookie ID). Why?

- Simpler for example code
- Real Netflix would need deterministic ID linking
- Demonstrates understanding of the problem

---

## Performance Considerations

### Table Partitioning

In production, tables would be partitioned by `event_date`:

```sql
PARTITION BY event_date
CLUSTER BY campaign_id, channel
```

This:
- **Limits scan cost**: Queries filtered by date only scan relevant partitions
- **Improves CTR**: Related campaigns are stored together

### Incremental Loads

The design supports **incremental loading**:

```sql
WHERE event_timestamp >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
```

This:
- Only processes yesterday's data on daily runs
- Scales as data volume grows
- Backfill-friendly (recompute entire period if needed)

### Materialized Mart vs. Views

I chose **materialized tables** (not views) for marts because:

- Queries are predictable and fast
- Can be queried by BI tools independently
- Allow for aggregation without requiring source tables

---

## If I Had More Time

### 1. Real-time Attribution (Streaming)

Current design is **batch** (daily aggregation). Streaming alternative:
- Kafka → Dataflow → BigTable → Real-time dashboards
- Trade-off: Complexity vs. freshness

### 2. Incrementality Testing

This project focuses on **observational analysis**. Incrementality testing (holdout groups) would:
- Use causal inference to separate correlation from causation
- Require experimental design (random holdout generation)
- More sophisticated but also more powerful

### 3. ML-Based Budget Optimization

Current optimizer uses **simple heuristics**. ML alternative:
- Learn channel elasticity from historical data
- Predict optimal allocation using multi-armed bandits
- Complex to implement; might not beat heuristics

### 4. Privacy-Preserving Attribution

As privacy shifts, would implement:
- Differential privacy (noise injection to protect individuals)
- Cross-device matching without PII
- Aggregated data reporting (Apple Privacy-Preserving AD Click Attribution)

---

## Lessons Learned

### 1. SQL > Pandas for Aggregations at Scale

I wrote mart metrics in SQL (not Python). Why?
- SQL naturally expresses grouped aggregations
- Runs in-database (no data movement to Python)
- dbt provides version control and testing

### 2. Attribution is Hard; Communication is Harder

Multiple attribution models → "Which one do I trust?"

Solution:
- **Transparent naming**: `last_touch`, `first_touch`, `time_decay` are unambiguous
- **Recommendation**: Document which to use for which decision
- **Validation**: Show how they differ (divergence analysis)

### 3. Configuration Beats Magic Numbers

Every hardcoded value (attribution window, half-life) belongs in config.

Example issue: "Why only 28-day window?"
Answer is in `pipeline_config.yaml`, not comments.

---

## Conclusion

This project demonstrates **production-quality analytics engineering** by:

1. Using industry-standard patterns (dbt staging/marts)
2. Making deliberate tradeoffs (explained above)
3. Writing for two audiences (engineers, analysts)
4. Building testable, maintainable code
5. Focusing on clarity over cleverness

The architecture scales from portfolio project to production Netflix Ads platform with minimal changes—just swap synthetic data for real BigQuery sources.

---

**Contact**: pranavmodem@gmail.com
