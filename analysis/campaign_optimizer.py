#!/usr/bin/env python3
"""
Campaign Performance Optimizer
Analyzes campaign metrics and recommends budget reallocations.
"""

import json
import random
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple


@dataclass
class CampaignMetrics:
    """Campaign performance metrics"""
    campaign_id: str
    channel: str
    spend: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float
    days_active: int

    @property
    def cpm(self) -> float:
        """Cost Per Mille (cost per 1000 impressions)"""
        if self.impressions == 0:
            return 0
        return (self.spend / self.impressions) * 1000

    @property
    def ctr(self) -> float:
        """Click-Through Rate"""
        if self.impressions == 0:
            return 0
        return self.clicks / self.impressions

    @property
    def cpc(self) -> float:
        """Cost Per Click"""
        if self.clicks == 0:
            return 0
        return self.spend / self.clicks

    @property
    def cpa(self) -> float:
        """Cost Per Acquisition"""
        if self.conversions == 0:
            return 0
        return self.spend / self.conversions

    @property
    def roas(self) -> float:
        """Return On Ad Spend"""
        if self.spend == 0:
            return 0
        return self.revenue / self.spend

    @property
    def cvr(self) -> float:
        """Conversion Rate"""
        if self.clicks == 0:
            return 0
        return self.conversions / self.clicks

    @property
    def aov(self) -> float:
        """Average Order Value"""
        if self.conversions == 0:
            return 0
        return self.revenue / self.conversions

    def to_dict(self) -> Dict:
        """Convert to dict with computed metrics"""
        d = asdict(self)
        d.update({
            "cpm": round(self.cpm, 2),
            "ctr": round(self.ctr * 100, 2),  # as percentage
            "cpc": round(self.cpc, 2),
            "cpa": round(self.cpa, 2),
            "roas": round(self.roas, 2),
            "cvr": round(self.cvr * 100, 2),  # as percentage
            "aov": round(self.aov, 2),
        })
        return d


def generate_sample_campaigns() -> List[CampaignMetrics]:
    """Generate realistic campaign data"""
    random.seed(42)

    campaigns_spec = [
        ("SEM_Q1", "Search", 5000),
        ("SEM_Q2", "Search", 4500),
        ("DSP_Awareness", "Display", 3000),
        ("DSP_Retargeting", "Display", 6000),
        ("YouTube_Preroll", "Video", 4000),
        ("YouTube_Discovery", "Video", 3500),
        ("Facebook_Feed", "Social", 2500),
        ("Instagram_Stories", "Social", 2000),
    ]

    campaigns = []

    for campaign_id, channel, daily_budget in campaigns_spec:
        days_active = random.randint(20, 30)
        total_spend = daily_budget * days_active

        # Channel-specific performance patterns
        if channel == "Search":
            impr_multiplier = random.uniform(0.8, 1.2)
            ctr = random.uniform(0.03, 0.05)
            cvr = random.uniform(0.08, 0.12)
        elif channel == "Display":
            impr_multiplier = random.uniform(1.5, 2.5)
            ctr = random.uniform(0.008, 0.015)
            cvr = random.uniform(0.02, 0.04)
        elif channel == "Video":
            impr_multiplier = random.uniform(1.2, 1.8)
            ctr = random.uniform(0.015, 0.03)
            cvr = random.uniform(0.04, 0.07)
        else:  # Social
            impr_multiplier = random.uniform(1.0, 1.5)
            ctr = random.uniform(0.01, 0.025)
            cvr = random.uniform(0.03, 0.06)

        impressions = int(total_spend * impr_multiplier / (random.uniform(2, 6)))
        clicks = int(impressions * ctr)
        conversions = int(clicks * cvr)
        aov = random.uniform(30, 150)
        revenue = conversions * aov

        campaigns.append(CampaignMetrics(
            campaign_id=campaign_id,
            channel=channel,
            spend=total_spend,
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            revenue=revenue,
            days_active=days_active,
        ))

    return campaigns


def compute_performance_tiers(campaigns: List[CampaignMetrics]) -> Dict[str, List[CampaignMetrics]]:
    """Categorize campaigns by performance tier"""
    # Use ROAS as primary metric
    campaigns_sorted = sorted(campaigns, key=lambda c: c.roas, reverse=True)

    tiers = {
        "top_performers": campaigns_sorted[:2],
        "mid_performers": campaigns_sorted[2:5],
        "underperformers": campaigns_sorted[5:],
    }

    return tiers


def identify_optimization_opportunities(campaigns: List[CampaignMetrics]) -> Dict:
    """Identify specific optimization opportunities"""

    opportunities = {
        "high_cpa_campaigns": [],
        "low_ctr_campaigns": [],
        "high_spend_low_roi": [],
        "channel_winners": {},
        "scaling_candidates": [],
    }

    # Calculate median metrics for benchmarking
    cpa_values = [c.cpa for c in campaigns if c.conversions > 0]
    ctr_values = [c.ctr for c in campaigns]
    roas_values = [c.roas for c in campaigns]

    median_cpa = sorted(cpa_values)[len(cpa_values) // 2] if cpa_values else 0
    median_ctr = sorted(ctr_values)[len(ctr_values) // 2]
    median_roas = sorted(roas_values)[len(roas_values) // 2]

    for campaign in campaigns:
        # High CPA opportunities
        if campaign.conversions > 0 and campaign.cpa > median_cpa * 1.5:
            opportunities["high_cpa_campaigns"].append({
                "campaign": campaign.campaign_id,
                "current_cpa": round(campaign.cpa, 2),
                "median_cpa": round(median_cpa, 2),
                "recommendation": "Review targeting, landing pages, or bid strategy"
            })

        # Low CTR opportunities
        if campaign.ctr < median_ctr * 0.7:
            opportunities["low_ctr_campaigns"].append({
                "campaign": campaign.campaign_id,
                "current_ctr": round(campaign.ctr * 100, 2),
                "median_ctr": round(median_ctr * 100, 2),
                "recommendation": "Refresh ad creatives or improve targeting"
            })

        # High spend, low ROI
        if campaign.roas < median_roas * 0.8 and campaign.spend > 4000:
            opportunities["high_spend_low_roi"].append({
                "campaign": campaign.campaign_id,
                "spend": round(campaign.spend, 2),
                "roas": round(campaign.roas, 2),
                "recommendation": "Consider pausing or significantly optimizing"
            })

    # Best channels
    channel_performance = {}
    for campaign in campaigns:
        if campaign.channel not in channel_performance:
            channel_performance[campaign.channel] = []
        channel_performance[campaign.channel].append(campaign.roas)

    for channel, roas_list in channel_performance.items():
        opportunities["channel_winners"][channel] = {
            "avg_roas": round(sum(roas_list) / len(roas_list), 2),
            "num_campaigns": len(roas_list),
        }

    # Scaling candidates (high ROAS, room to grow)
    for campaign in campaigns:
        if campaign.roas > median_roas * 1.2:
            opportunities["scaling_candidates"].append({
                "campaign": campaign.campaign_id,
                "current_roas": round(campaign.roas, 2),
                "current_spend": round(campaign.spend, 2),
                "potential_10pct_increase_revenue": round(campaign.revenue * 0.1, 2),
            })

    return opportunities


def recommend_budget_allocation(campaigns: List[CampaignMetrics], total_budget: float) -> Dict:
    """Recommend optimal budget allocation"""

    # Use weighted scoring: ROAS (50%), efficiency (CTR/CPA, 30%), growth potential (20%)
    def score_campaign(c: CampaignMetrics) -> float:
        roas_score = c.roas / max([cam.roas for cam in campaigns])
        efficiency_score = (c.ctr * 100) / max([cam.ctr * 100 for cam in campaigns])
        growth_potential = (c.conversions / max([cam.conversions for cam in campaigns])) if campaigns else 0

        return (roas_score * 0.5) + (efficiency_score * 0.3) + (growth_potential * 0.2)

    campaign_scores = [(c, score_campaign(c)) for c in campaigns]
    campaign_scores.sort(key=lambda x: x[1], reverse=True)

    total_score = sum(score for _, score in campaign_scores)

    allocations = []
    for campaign, score in campaign_scores:
        allocation = (score / total_score) * total_budget
        allocations.append({
            "campaign": campaign.campaign_id,
            "channel": campaign.channel,
            "recommended_budget": round(allocation, 2),
            "current_budget": round(campaign.spend, 2),
            "change_pct": round(((allocation - campaign.spend) / campaign.spend * 100), 1),
            "expected_roas": round(campaign.roas, 2),
        })

    return {
        "total_budget": total_budget,
        "allocations": allocations,
    }


def main():
    """Main entry point"""
    print("Generating campaign data...")
    campaigns = generate_sample_campaigns()
    print(f"Loaded {len(campaigns)} campaigns\n")

    print("="*80)
    print("CAMPAIGN PERFORMANCE METRICS")
    print("="*80)
    for campaign in campaigns:
        metrics = campaign.to_dict()
        print(f"\n{campaign.campaign_id}:")
        print(f"  Channel: {campaign.channel}")
        print(f"  Spend: ${metrics['spend']:,.0f} | Revenue: ${metrics['revenue']:,.0f}")
        print(f"  ROAS: {metrics['roas']}x | CPA: ${metrics['cpa']}")
        print(f"  CTR: {metrics['ctr']}% | CVR: {metrics['cvr']}% | CPM: ${metrics['cpm']}")

    print("\n" + "="*80)
    print("PERFORMANCE TIERS")
    print("="*80)
    tiers = compute_performance_tiers(campaigns)

    for tier_name, tier_campaigns in tiers.items():
        print(f"\n{tier_name.upper()}:")
        for c in tier_campaigns:
            print(f"  {c.campaign_id}: ROAS {c.roas:.2f}x, Spend ${c.spend:,.0f}")

    print("\n" + "="*80)
    print("OPTIMIZATION OPPORTUNITIES")
    print("="*80)
    opportunities = identify_optimization_opportunities(campaigns)

    if opportunities["high_cpa_campaigns"]:
        print("\nHigh CPA Campaigns (optimize targeting/creatives):")
        for opp in opportunities["high_cpa_campaigns"]:
            print(f"  {opp['campaign']}: ${opp['current_cpa']} CPA (vs ${opp['median_cpa']} median)")

    if opportunities["low_ctr_campaigns"]:
        print("\nLow CTR Campaigns (refresh creatives):")
        for opp in opportunities["low_ctr_campaigns"]:
            print(f"  {opp['campaign']}: {opp['current_ctr']}% CTR (vs {opp['median_ctr']}% median)")

    if opportunities["scaling_candidates"]:
        print("\nScaling Candidates (high ROAS, increase budget):")
        for opp in opportunities["scaling_candidates"]:
            print(f"  {opp['campaign']}: {opp['current_roas']}x ROAS, +${opp['potential_10pct_increase_revenue']} potential")

    print("\n" + "="*80)
    print("BUDGET REALLOCATION RECOMMENDATION")
    print("="*80)
    total_spend = sum(c.spend for c in campaigns)
    allocation = recommend_budget_allocation(campaigns, total_spend)

    print(f"\nTotal Budget: ${allocation['total_budget']:,.0f}")
    print("\nRecommended Allocation:")
    for alloc in allocation["allocations"]:
        change = f"({alloc['change_pct']:+.1f}%)" if alloc['change_pct'] != 0 else "(no change)"
        print(f"  {alloc['campaign']}: ${alloc['recommended_budget']:,.0f} {change}")

    # Save results
    output = {
        "campaigns": [c.to_dict() for c in campaigns],
        "performance_tiers": {
            tier: [c.campaign_id for c in tier_campaigns]
            for tier, tier_campaigns in tiers.items()
        },
        "optimization_opportunities": opportunities,
        "budget_allocation": allocation,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_campaigns": len(campaigns),
            "total_spend": round(total_spend, 2),
        }
    }

    with open("campaign_optimization_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\nResults saved to campaign_optimization_results.json")


if __name__ == "__main__":
    main()
