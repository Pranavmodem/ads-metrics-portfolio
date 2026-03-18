#!/usr/bin/env python3
"""
Attribution Model Analysis
Compares multiple attribution models (last-touch, first-touch, linear, time-decay)
on synthetic ad campaign data.
"""

import json
import math
import random
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class TouchPoint:
    """Represents a single ad impression/touch"""
    timestamp: datetime
    channel: str
    campaign_id: str
    cost: float


@dataclass
class Conversion:
    """Represents a user conversion"""
    user_id: str
    conversion_value: float
    timestamp: datetime
    touches: List[TouchPoint]


class AttributionModels:
    """Collection of attribution models"""

    @staticmethod
    def last_touch(conversion: Conversion) -> Dict[str, float]:
        """Last-touch attribution: all credit to final interaction"""
        if not conversion.touches:
            return {}

        last = conversion.touches[-1]
        return {
            f"{last.channel}_{last.campaign_id}": conversion.conversion_value
        }

    @staticmethod
    def first_touch(conversion: Conversion) -> Dict[str, float]:
        """First-touch attribution: all credit to first interaction"""
        if not conversion.touches:
            return {}

        first = conversion.touches[0]
        return {
            f"{first.channel}_{first.campaign_id}": conversion.conversion_value
        }

    @staticmethod
    def linear(conversion: Conversion) -> Dict[str, float]:
        """Linear attribution: equal credit to all touches"""
        if not conversion.touches:
            return {}

        credit = conversion.conversion_value / len(conversion.touches)
        result = {}
        for touch in conversion.touches:
            key = f"{touch.channel}_{touch.campaign_id}"
            result[key] = result.get(key, 0) + credit
        return result

    @staticmethod
    def time_decay(conversion: Conversion, half_life_days: float = 7) -> Dict[str, float]:
        """Time-decay attribution: exponential decay based on recency"""
        if not conversion.touches:
            return {}

        # Convert all timestamps to days from conversion
        conversion_seconds = conversion.timestamp.timestamp()
        weights = []

        for touch in conversion.touches:
            days_before = (conversion_seconds - touch.timestamp.timestamp()) / (24 * 3600)
            # Weight = 2^(-days / half_life)
            weight = 2 ** (-days_before / half_life_days)
            weights.append(weight)

        total_weight = sum(weights)
        if total_weight == 0:
            return self.linear(conversion)

        result = {}
        for touch, weight in zip(conversion.touches, weights):
            key = f"{touch.channel}_{touch.campaign_id}"
            credit = (weight / total_weight) * conversion.conversion_value
            result[key] = result.get(key, 0) + credit

        return result


def generate_synthetic_data(num_users: int = 1000, seed: int = 42) -> List[Conversion]:
    """Generate realistic synthetic conversion data with multi-touch journeys"""
    random.seed(seed)

    channels = ["Search", "Display", "Video", "Social"]
    campaigns = {
        "Search": ["SEM_Q1", "SEM_Q2"],
        "Display": ["DSP_Awareness", "DSP_Retargeting"],
        "Video": ["YouTube_Preroll", "YouTube_Discovery"],
        "Social": ["Facebook_Feed", "Instagram_Stories"]
    }

    conversions = []
    base_time = datetime(2024, 1, 1)

    for user_id in range(num_users):
        # Random journey length (1-5 touches)
        num_touches = random.choices([1, 2, 3, 4, 5], weights=[0.2, 0.3, 0.3, 0.15, 0.05])[0]

        # Generate touches
        touches = []
        current_time = base_time + timedelta(days=random.randint(0, 89))

        for _ in range(num_touches):
            channel = random.choice(channels)
            campaign = random.choice(campaigns[channel])
            cost = random.uniform(0.5, 5.0)

            touches.append(TouchPoint(
                timestamp=current_time,
                channel=channel,
                campaign_id=campaign,
                cost=cost
            ))

            # Next touch 1-7 days later
            current_time += timedelta(days=random.randint(1, 7))

        # Conversion happens 0-3 days after last touch
        conversion_time = current_time + timedelta(days=random.randint(0, 3))
        conversion_value = random.choices(
            [25, 50, 100, 250],
            weights=[0.4, 0.35, 0.2, 0.05]
        )[0]

        conversions.append(Conversion(
            user_id=f"user_{user_id}",
            conversion_value=conversion_value,
            timestamp=conversion_time,
            touches=touches
        ))

    return conversions


def analyze_attributions(conversions: List[Conversion]) -> Dict:
    """Run all attribution models and generate comparison statistics"""

    models = {
        "last_touch": AttributionModels.last_touch,
        "first_touch": AttributionModels.first_touch,
        "linear": AttributionModels.linear,
        "time_decay": AttributionModels.time_decay,
    }

    results = {}

    for model_name, model_func in models.items():
        channel_credit = {}
        campaign_credit = {}

        for conversion in conversions:
            attribution = model_func(conversion)

            for touch_key, credit in attribution.items():
                channel, campaign = touch_key.rsplit("_", 1)
                if len(touch_key.split("_")) > 2:
                    # Handle multi-word campaign names
                    parts = touch_key.split("_")
                    channel = parts[0]
                    campaign = "_".join(parts[1:])

                channel_credit[channel] = channel_credit.get(channel, 0) + credit
                campaign_credit[campaign] = campaign_credit.get(campaign, 0) + credit

        total_attributed = sum(channel_credit.values())

        results[model_name] = {
            "total_attributed_revenue": total_attributed,
            "channel_breakdown": dict(sorted(
                channel_credit.items(),
                key=lambda x: x[1],
                reverse=True
            )),
            "campaign_breakdown": dict(sorted(
                campaign_credit.items(),
                key=lambda x: x[1],
                reverse=True
            )),
            "top_channel": max(channel_credit.items(), key=lambda x: x[1])[0] if channel_credit else None,
            "conversion_count": len(conversions),
        }

    return results


def compute_comparison_stats(results: Dict) -> Dict:
    """Generate comparison statistics across models"""

    stats = {
        "model_comparison": {},
        "channel_consensus": {},
        "divergence_analysis": {}
    }

    # Model comparison
    for model_name, model_data in results.items():
        stats["model_comparison"][model_name] = {
            "total_revenue": model_data["total_attributed_revenue"],
            "top_channel": model_data["top_channel"],
        }

    # Channel consensus: which channels appear in top 2 across models
    all_top_channels = []
    for model_data in results.values():
        top_channels = sorted(
            model_data["channel_breakdown"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:2]
        all_top_channels.extend([ch[0] for ch in top_channels])

    channel_consensus = {}
    for channel in set(all_top_channels):
        count = all_top_channels.count(channel)
        channel_consensus[channel] = {
            "appears_in_top_2": count,
            "models": len(results)
        }

    stats["channel_consensus"] = dict(sorted(
        channel_consensus.items(),
        key=lambda x: x[1]["appears_in_top_2"],
        reverse=True
    ))

    # Divergence: compute variance of channel credit across models
    all_channels = set()
    for model_data in results.values():
        all_channels.update(model_data["channel_breakdown"].keys())

    for channel in sorted(all_channels):
        credits = [
            results[model]["channel_breakdown"].get(channel, 0)
            for model in results.keys()
        ]
        mean_credit = sum(credits) / len(credits) if credits else 0
        variance = sum((c - mean_credit) ** 2 for c in credits) / len(credits) if credits else 0
        std_dev = math.sqrt(variance)

        stats["divergence_analysis"][channel] = {
            "mean_credit": round(mean_credit, 2),
            "std_dev": round(std_dev, 2),
            "min_credit": min(credits) if credits else 0,
            "max_credit": max(credits) if credits else 0,
        }

    return stats


def main():
    """Main entry point"""
    print("Generating synthetic data...")
    conversions = generate_synthetic_data(num_users=1000)
    print(f"Generated {len(conversions)} conversions")

    print("\nRunning attribution models...")
    results = analyze_attributions(conversions)

    print("\nComputing comparison statistics...")
    stats = compute_comparison_stats(results)

    # Print results
    print("\n" + "="*80)
    print("ATTRIBUTION MODEL ANALYSIS RESULTS")
    print("="*80)

    for model_name, model_data in results.items():
        print(f"\n{model_name.upper()}:")
        print(f"  Total Attributed Revenue: ${model_data['total_attributed_revenue']:,.2f}")
        print(f"  Top Channel: {model_data['top_channel']}")
        print(f"  Channel Breakdown:")
        for channel, value in list(model_data['channel_breakdown'].items())[:3]:
            print(f"    {channel}: ${value:,.2f}")

    print("\n" + "="*80)
    print("CHANNEL CONSENSUS")
    print("="*80)
    for channel, consensus in stats["channel_consensus"].items():
        print(f"{channel}: Top-2 in {consensus['appears_in_top_2']}/{consensus['models']} models")

    print("\n" + "="*80)
    print("ATTRIBUTION DIVERGENCE (Standard Deviation Across Models)")
    print("="*80)
    for channel, div_stats in sorted(
        stats["divergence_analysis"].items(),
        key=lambda x: x[1]["std_dev"],
        reverse=True
    ):
        print(f"{channel}:")
        print(f"  Mean Credit: ${div_stats['mean_credit']:,.2f}")
        print(f"  Std Dev: ${div_stats['std_dev']:,.2f}")
        print(f"  Range: ${div_stats['min_credit']:.2f} - ${div_stats['max_credit']:,.2f}")

    # Save results as JSON
    output = {
        "attribution_results": results,
        "comparison_stats": stats,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "num_conversions": len(conversions),
        }
    }

    with open("attribution_results.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    print("\nResults saved to attribution_results.json")


if __name__ == "__main__":
    main()
