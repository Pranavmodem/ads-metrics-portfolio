#!/usr/bin/env python3
"""
A/B Test Statistical Calculator
Computes significance, confidence intervals, and sample size requirements.
"""

import math
import json
from dataclasses import dataclass
from typing import Tuple, Dict


@dataclass
class ABTestResult:
    """Result of an A/B test"""
    control_conversions: int
    control_visitors: int
    variant_conversions: int
    variant_visitors: int
    significance_level: float = 0.05  # 95% confidence

    @property
    def control_rate(self) -> float:
        """Control conversion rate"""
        return self.control_conversions / self.control_visitors if self.control_visitors > 0 else 0

    @property
    def variant_rate(self) -> float:
        """Variant conversion rate"""
        return self.variant_conversions / self.variant_visitors if self.variant_visitors > 0 else 0

    @property
    def relative_lift(self) -> float:
        """Relative lift of variant vs control"""
        if self.control_rate == 0:
            return 0
        return (self.variant_rate - self.control_rate) / self.control_rate

    def z_score(self) -> float:
        """Calculate z-score for two-proportion z-test"""
        # Pooled proportion
        p_pool = (self.control_conversions + self.variant_conversions) / \
                 (self.control_visitors + self.variant_visitors)

        if p_pool == 0 or p_pool == 1:
            return 0

        # Standard error
        se = math.sqrt(
            p_pool * (1 - p_pool) * (1/self.control_visitors + 1/self.variant_visitors)
        )

        if se == 0:
            return 0

        # Z-score
        z = (self.variant_rate - self.control_rate) / se
        return z

    def p_value(self) -> float:
        """Calculate two-tailed p-value"""
        try:
            from scipy import stats
            # Two-proportion z-test
            z = self.z_score()
            p = 2 * (1 - stats.norm.cdf(abs(z)))
            return p
        except ImportError:
            return None

    def is_significant(self) -> bool:
        """Is the result statistically significant?"""
        try:
            return self.p_value() < self.significance_level
        except:
            return False

    def confidence_interval(self, confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for lift"""
        z_critical = 1.96 if confidence == 0.95 else 2.576  # 99% CI

        # Standard error of the difference
        se = math.sqrt(
            (self.control_rate * (1 - self.control_rate) / self.control_visitors) +
            (self.variant_rate * (1 - self.variant_rate) / self.variant_visitors)
        )

        margin_error = z_critical * se
        lower = self.variant_rate - self.control_rate - margin_error
        upper = self.variant_rate - self.control_rate + margin_error

        return (lower, upper)


class SampleSizeCalculator:
    """Calculate required sample sizes for A/B tests"""

    @staticmethod
    def required_sample_size(
        baseline_rate: float,
        minimum_detectable_effect: float,
        significance_level: float = 0.05,
        power: float = 0.8
    ) -> int:
        """
        Calculate required sample size per group.

        Args:
            baseline_rate: Baseline conversion rate (e.g., 0.05)
            minimum_detectable_effect: Minimum lift to detect (e.g., 0.15 for 15%)
            significance_level: Type I error rate (default 0.05 for 95% confidence)
            power: Statistical power (default 0.8 for 80% power)

        Returns:
            Required sample size per group
        """
        try:
            from scipy import stats

            # Effect size (Cohen's h)
            control_rate = baseline_rate
            variant_rate = baseline_rate * (1 + minimum_detectable_effect)

            h = 2 * (math.asin(math.sqrt(variant_rate)) - math.asin(math.sqrt(control_rate)))

            # Z-scores
            z_alpha = stats.norm.ppf(1 - significance_level / 2)  # Two-tailed
            z_beta = stats.norm.ppf(power)

            # Sample size formula
            n = ((z_alpha + z_beta) ** 2 * 2) / (h ** 2)

            return math.ceil(n)
        except ImportError:
            # Fallback: use approximation without scipy
            # Using rule of thumb: n = 16 / (effect_size^2) for 0.05 significance, 0.8 power
            effect_pct = abs(minimum_detectable_effect)
            return max(int(1000 / (effect_pct ** 2)), 100)

    @staticmethod
    def required_duration(
        daily_visitors: int,
        sample_size_per_group: int,
        traffic_split: float = 0.5
    ) -> float:
        """
        Calculate required test duration.

        Args:
            daily_visitors: Daily visitors to your site
            sample_size_per_group: Required sample size per group
            traffic_split: Percentage of traffic for variant (default 0.5 for 50/50 split)

        Returns:
            Required duration in days
        """
        variant_daily_visitors = daily_visitors * traffic_split
        days_required = sample_size_per_group / variant_daily_visitors
        return days_required


def analyze_test(test: ABTestResult) -> Dict:
    """Analyze an A/B test result"""

    # Confidence interval for lift
    ci_lower, ci_upper = test.confidence_interval()

    # Try to get p-value, fallback if scipy not available
    try:
        p_val = test.p_value()
        is_sig = test.is_significant()
    except:
        p_val = None
        is_sig = None

    return {
        "control": {
            "visitors": test.control_visitors,
            "conversions": test.control_conversions,
            "conversion_rate": round(test.control_rate * 100, 3),
        },
        "variant": {
            "visitors": test.variant_visitors,
            "conversions": test.variant_conversions,
            "conversion_rate": round(test.variant_rate * 100, 3),
        },
        "results": {
            "absolute_lift": round((test.variant_rate - test.control_rate) * 100, 3),
            "relative_lift_pct": round(test.relative_lift * 100, 2),
            "z_score": round(test.z_score(), 3),
            "p_value": round(p_val, 4) if p_val else None,
            "is_significant": is_sig,
            "confidence_interval_lower": round(ci_lower * 100, 3),
            "confidence_interval_upper": round(ci_upper * 100, 3),
        },
        "interpretation": interpret_result(test, p_val if p_val else None, is_sig)
    }


def interpret_result(test: ABTestResult, p_value: float = None, is_significant: bool = None) -> str:
    """Generate human-readable interpretation"""
    if is_significant is False:
        return "Result is NOT statistically significant. Continue testing or accept that there's no meaningful difference."
    elif is_significant is True:
        if test.relative_lift > 0:
            return f"Variant is {test.relative_lift*100:.1f}% better than control. Statistically significant. Consider rolling out."
        else:
            return f"Variant is {abs(test.relative_lift)*100:.1f}% worse than control. Statistically significant. Stick with control."
    else:
        # Fallback interpretation
        if test.relative_lift > 0.05:
            return "Variant shows potential improvement, but results may not be statistically significant yet."
        elif test.relative_lift < -0.05:
            return "Variant shows potential decline. Consider pausing test."
        else:
            return "No meaningful difference detected between control and variant."


def main():
    """Main entry point with example tests"""
    print("="*80)
    print("A/B TEST STATISTICAL CALCULATOR")
    print("="*80)

    # Example 1: Ad copy test
    print("\n[TEST 1] Ad Copy A/B Test")
    print("-" * 80)
    test1 = ABTestResult(
        control_conversions=150,
        control_visitors=5000,
        variant_conversions=180,
        variant_visitors=5000,
    )

    result1 = analyze_test(test1)
    print(f"Control Rate: {result1['control']['conversion_rate']}%")
    print(f"Variant Rate: {result1['variant']['conversion_rate']}%")
    print(f"Absolute Lift: {result1['results']['absolute_lift']}%")
    print(f"Relative Lift: {result1['results']['relative_lift_pct']}%")
    print(f"P-value: {result1['results']['p_value']}")
    print(f"Significant: {result1['results']['is_significant']}")
    print(f"95% CI: [{result1['results']['confidence_interval_lower']}%, {result1['results']['confidence_interval_upper']}%]")
    print(f"Interpretation: {result1['interpretation']}")

    # Example 2: Landing page test
    print("\n[TEST 2] Landing Page Design Test")
    print("-" * 80)
    test2 = ABTestResult(
        control_conversions=85,
        control_visitors=10000,
        variant_conversions=92,
        variant_visitors=10000,
    )

    result2 = analyze_test(test2)
    print(f"Control Rate: {result2['control']['conversion_rate']}%")
    print(f"Variant Rate: {result2['variant']['conversion_rate']}%")
    print(f"Absolute Lift: {result2['results']['absolute_lift']}%")
    print(f"Relative Lift: {result2['results']['relative_lift_pct']}%")
    print(f"P-value: {result2['results']['p_value']}")
    print(f"Significant: {result2['results']['is_significant']}")
    print(f"95% CI: [{result2['results']['confidence_interval_lower']}%, {result2['results']['confidence_interval_upper']}%]")
    print(f"Interpretation: {result2['interpretation']}")

    # Example 3: CTA button test
    print("\n[TEST 3] CTA Button Color Test")
    print("-" * 80)
    test3 = ABTestResult(
        control_conversions=45,
        control_visitors=5000,
        variant_conversions=38,
        variant_visitors=5000,
    )

    result3 = analyze_test(test3)
    print(f"Control Rate: {result3['control']['conversion_rate']}%")
    print(f"Variant Rate: {result3['variant']['conversion_rate']}%")
    print(f"Absolute Lift: {result3['results']['absolute_lift']}%")
    print(f"Relative Lift: {result3['results']['relative_lift_pct']}%")
    print(f"P-value: {result3['results']['p_value']}")
    print(f"Significant: {result3['results']['is_significant']}")
    print(f"95% CI: [{result3['results']['confidence_interval_lower']}%, {result3['results']['confidence_interval_upper']}%]")
    print(f"Interpretation: {result3['interpretation']}")

    # Sample size calculations
    print("\n" + "="*80)
    print("SAMPLE SIZE REQUIREMENTS")
    print("="*80)

    scenarios = [
        (0.03, 0.15, "Low baseline (3%), 15% lift desired"),
        (0.05, 0.10, "Medium baseline (5%), 10% lift desired"),
        (0.10, 0.10, "High baseline (10%), 10% lift desired"),
    ]

    for baseline, effect, description in scenarios:
        sample_size = SampleSizeCalculator.required_sample_size(baseline, effect)
        duration = SampleSizeCalculator.required_duration(50000, sample_size)

        print(f"\n{description}")
        print(f"  Baseline Rate: {baseline*100}%")
        print(f"  Minimum Detectable Effect: {effect*100}%")
        print(f"  Required Sample Size (per group): {sample_size:,}")
        print(f"  Duration (at 50K daily visitors, 50/50 split): {duration:.1f} days")

    # Save results
    output = {
        "tests": [
            {"name": "Ad Copy Test", "result": result1},
            {"name": "Landing Page Test", "result": result2},
            {"name": "CTA Button Test", "result": result3},
        ],
        "sample_size_guidance": [
            {
                "baseline_rate": s[0],
                "minimum_detectable_effect": s[1],
                "description": s[2],
                "sample_size_per_group": SampleSizeCalculator.required_sample_size(s[0], s[1]),
                "days_at_50k_daily": round(SampleSizeCalculator.required_duration(50000, SampleSizeCalculator.required_sample_size(s[0], s[1])), 1),
            }
            for s in scenarios
        ],
        "metadata": {
            "timestamp": datetime.now().isoformat(),
        }
    }

    with open("ab_test_results.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    print("\nResults saved to ab_test_results.json")


if __name__ == "__main__":
    from datetime import datetime
    main()
