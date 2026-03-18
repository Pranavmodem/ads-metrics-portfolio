# Analytics Engineering Portfolio

**Pranav Modem** (pranavmodem@gmail.com) | Senior Analytics Engineer

## Overview

A production-grade analytics engineering project demonstrating end-to-end expertise in ad metrics, data modeling, statistical analysis, and campaign optimization for advertising platforms at scale.

This portfolio includes:
- **Interactive Dashboard** (`index.html`) — Visual exploration of ad metrics and attribution models
- **Production Data Models** (`sql/`) — dbt-style staging and mart models for BigQuery
- **Statistical Analysis** (`analysis/`) — Attribution modeling, campaign optimization, A/B testing
- **Comprehensive Tests** (`tests/`) — Unit tests validating core logic
- **Reference Documentation** (`docs/`) — Metrics catalog and design decisions

## Project Structure

```
.
├── index.html                          # Interactive dashboard (frontend)
├── README.md                           # This file
├── Makefile                            # Task automation
├── requirements.txt                    # Python dependencies
├── .gitignore                          # Git configuration
│
├── analysis/                           # Statistical analysis scripts
│   ├── attribution_analysis.py         # Multi-touch attribution (4 models)
│   ├── campaign_optimizer.py           # Campaign performance & budget allocation
│   └── ab_test_calculator.py           # A/B testing (z-test, sample size, CI)
│
├── sql/                                # dbt-style data models
│   ├── staging_impressions.sql         # Impression deduplication & cleaning
│   ├── staging_conversions.sql         # Conversion validation & late arrivals
│   ├── mart_campaign_metrics.sql       # Business metrics (CPM, CTR, ROAS, CPA, etc)
│   └── mart_attribution_summary.sql    # Attribution results by model & channel
│
├── tests/                              # Unit tests
│   ├── test_attribution.py             # Attribution model validation
│   └── test_ab_calculator.py           # Statistical tests
│
├── data/                               # Sample data
│   ├── sample_impressions.csv          # 50 synthetic impression events
│   └── sample_conversions.csv          # 20 synthetic conversion events
│
├── config/                             # Configuration files
│   ├── pipeline_config.yaml            # Pipeline settings (BigQuery, attribution window)
│   └── metrics_definitions.yaml        # Metric catalog with formulas
│
└── docs/                               # Documentation
    ├── metrics_catalog.md              # Comprehensive metrics reference
    └── design_decisions.md             # Architecture & tradeoffs
```

## Getting Started

### Installation

```bash
# Clone repository
git clone <repo>
cd ads-metrics-portfolio

# Create virtual environment
make setup

# Install dependencies
source venv/bin/activate
make install
```

### Running the Analysis

```bash
# Run all analyses
make run-analysis

# Or run individual scripts
make attribution          # Attribution model analysis → attribution_results.json
make optimization         # Campaign optimization → campaign_optimization_results.json
make ab-test             # A/B test calculator → ab_test_results.json
```

### Running Tests

```bash
# Run all tests
make test

# With coverage
make test-coverage
```

### Viewing the Dashboard

```bash
# Open interactive dashboard (no server required)
open index.html
```

### Validating Project

```bash
make validate            # Check project structure
make check-env          # Verify Python environment
```

## Core Components

### 1. Attribution Analysis (`analysis/attribution_analysis.py`)

Demonstrates multi-touch attribution modeling with:
- **4 attribution models**: Last-touch, First-touch, Linear, Time-decay
- **Synthetic journey data**: 1,000 users with 1-5 touches each
- **Comparison statistics**: Channel consensus, divergence analysis, model comparison
- **Output**: `attribution_results.json` with attribution breakdown by campaign and channel

```bash
python3 analysis/attribution_analysis.py
```

**Key insight**: Time-decay model gives 40%+ more credit to search vs. display (recency matters).

### 2. Campaign Optimizer (`analysis/campaign_optimizer.py`)

Analyzes campaign performance and recommends budget allocation:
- **8 realistic campaigns** across 4 channels (Search, Display, Video, Social)
- **Performance metrics**: ROAS, CPA, CTR, CVR, CPM, AOV, frequency
- **Opportunity identification**: High-CPA campaigns, low-CTR campaigns, scaling candidates
- **Budget reallocation**: Weighted scoring recommends optimal allocation
- **Output**: `campaign_optimization_results.json` with tier analysis and recommendations

```bash
python3 analysis/campaign_optimizer.py
```

**Example output**: "Allocate 35% of budget to YouTube Preroll (4.2x ROAS) vs 15% to Display Retargeting (1.8x ROAS)"

### 3. A/B Test Calculator (`analysis/ab_test_calculator.py`)

Statistical significance calculator for experiments:
- **3 test scenarios**: Ad copy, landing page, CTA button tests
- **Z-test for proportions**: Two-sample statistical test
- **Confidence intervals**: 95% and 99% CI for lift estimates
- **Sample size calculator**: Required sample sizes for different baselines/effects
- **Duration estimation**: Days needed at given traffic levels
- **Output**: `ab_test_results.json` with significance results and guidance

```bash
python3 analysis/ab_test_calculator.py
```

**Example**: "35,000 users per variant needed to detect 15% lift at 3% baseline with 95% confidence"

### 4. SQL Data Models (`sql/`)

Production-ready BigQuery models following dbt conventions:

**`staging_impressions.sql`**: Data quality layer
- Deduplicates impressions (row_number)
- Type-casts cost to FLOAT64
- Filters bot traffic (zero-cost impressions)
- Includes only last 90 days
- Generates surrogate keys

**`staging_conversions.sql`**: Conversion handling
- Late-arrival handling (up to 72 hours)
- Null validation
- Currency normalization (local → USD)
- Flags invalid records

**`mart_campaign_metrics.sql`**: Business metrics
- Joins impressions + conversions
- Computes 11 derived metrics in single pass:
  - **Efficiency**: CPM, CPC, CPA
  - **Engagement**: CTR, CVR, frequency
  - **ROI**: ROAS, AOV
  - **Operations**: Fill rate
- Grouped by campaign, channel, date

**`mart_attribution_summary.sql`**: Attribution results
- Multi-touch journeys (28-day window)
- 2 attribution models (last-touch, first-touch)
- Aggregated by channel and model
- Includes user count and revenue

### 5. Unit Tests (`tests/`)

**`test_attribution.py`**: 24 tests validating
- Single-touch and multi-touch handling
- Revenue preservation across all models
- Recency bias in time-decay
- Edge cases (zero values, old touches)

**`test_ab_calculator.py`**: 30 tests validating
- Conversion rate calculations
- Z-score computation
- Confidence intervals
- Sample size formulas
- Statistical significance

```bash
pytest tests/ -v
```

## Configuration

### `config/pipeline_config.yaml`

Central configuration for the entire pipeline:

```yaml
gcp:
  project_id: "netflix-ads-analytics"
  dataset: "ads_metrics_prod"

attribution:
  attribution_window_days: 28
  time_decay_half_life_days: 7
  models: [last_touch, first_touch, linear, time_decay]

optimization:
  allocation_method: "weighted_scoring"
  scoring_weights:
    roas: 0.5
    efficiency: 0.3
    growth_potential: 0.2
```

### `config/metrics_definitions.yaml`

Definitions for all business metrics:
- Formula
- Data source
- Business owner
- Benchmark
- Use cases
- Dimensions

## Documentation

### `docs/metrics_catalog.md`

Comprehensive reference (20+ pages) covering:
- **Efficiency metrics**: CPM, CPC, CPA (with formulas, benchmarks, use cases)
- **Engagement metrics**: CTR, CVR (with business context)
- **ROI metrics**: ROAS, AOV (with interpretation)
- **Reach metrics**: Impressions, unique users, frequency, fill rate
- **Attribution metrics**: Attributed revenue across models
- **Data quality rules**: Outlier thresholds, validation rules
- **Seasonality adjustments**: Holiday and seasonal factors
- **Usage guidelines**: When to use which metrics

### `docs/design_decisions.md`

Technical writeup (20+ pages) explaining:
- **Data modeling**: Why staging/mart pattern
- **Attribution architecture**: Why multiple models in parallel
- **Attribution window**: Why 28 days
- **Bot detection**: Rule-based vs ML
- **Python vs SQL**: When to use each
- **Testing philosophy**: Unit tests for Python, snapshot tests for SQL
- **Performance considerations**: Partitioning, incremental loads, materialization
- **If I had more time**: Real-time streaming, incrementality testing, ML optimization

## Sample Data

### `data/sample_impressions.csv`

50 synthetic impression events with realistic patterns:
- 5 campaigns across 4 channels (Search, Display, Video, Social)
- Realistic CPM by channel ($0.50-$2.80)
- Device mix (desktop, mobile, tablet)
- Timestamps spanning 1 week

### `data/sample_conversions.csv`

20 synthetic conversion events:
- Links users to campaigns
- Diverse conversion values ($25-$160)
- Different conversion types (purchase, subscription, trial)
- ~40% of users convert within 7 days of impression

## Skills Demonstrated

### Analytics & Metrics
- Metric design (20+ core metrics with formulas)
- Attribution modeling (4 different models with tradeoffs)
- Campaign analysis and optimization
- Statistical testing and sample size calculation
- Data quality validation

### Data Engineering
- dbt conventions (staging/mart pattern)
- BigQuery SQL at scale (handling late arrivals, deduplication, aggregation)
- Incremental data pipelines
- Data quality rules and monitoring

### Software Engineering
- Python with real data classes and type hints
- Unit testing with pytest
- Configuration management (YAML)
- Makefile automation
- Git best practices (.gitignore, clean structure)
- Code documentation (docstrings, README)

### Design & Communication
- Explaining complex concepts (attribution, statistical testing)
- First-person technical narrative (design decisions doc)
- Metrics catalog for non-technical audiences
- Clear code with meaningful variable names

## Metrics Highlights

### Attribution Model Comparison

The project includes a complete attribution analysis comparing:

| Model | Use Case | Bias |
|-------|----------|------|
| **Last-Touch** | "Which channel closes deals?" | Overvalues final click |
| **First-Touch** | "Which channel creates awareness?" | Undervalues nurturing |
| **Linear** | "Equal contribution" | Ignores journey dynamics |
| **Time-Decay** | "Recent interactions matter most" | Aligns with user behavior |

Time-decay recommended for most analyses with 7-day exponential half-life.

### Campaign Performance

8-campaign portfolio shows:
- ROAS range: 1.2x to 4.5x
- CPA range: $35 to $85
- CTR range: 0.8% to 5%
- Performance tiers with reallocation recommendations

### Statistical Rigor

A/B test calculator handles:
- Z-test for proportions (two-sample)
- 95% and 99% confidence intervals
- Sample size formulas (based on baseline, effect, power)
- Duration estimation at given traffic levels

## Production Readiness

This project is designed to scale from portfolio piece to a production ads analytics platform:

✓ **Tested**: 54 unit tests validating core logic
✓ **Documented**: Inline code comments + comprehensive guides
✓ **Modular**: Each component (analysis, models, tests) is independent
✓ **Configurable**: All hardcoded values in YAML config
✓ **Scalable**: SQL models partition and cluster for BigQuery performance
✓ **Maintainable**: Clear separation of concerns (staging/mart pattern)

## Running the Full Portfolio

```bash
# Setup
make setup

# Validate structure
make validate

# Run tests
make test

# Run analyses
make run-analysis

# View results
cat analysis/attribution_results.json
cat analysis/campaign_optimization_results.json
cat analysis/ab_test_results.json

# Open dashboard
open index.html
```

## Contact

**Pranav Modem**
Email: pranavmodem@gmail.com
Portfolio: This repository

---

*Demonstrates production-grade analytics engineering with real-world metrics, rigorous testing, and comprehensive documentation.*
