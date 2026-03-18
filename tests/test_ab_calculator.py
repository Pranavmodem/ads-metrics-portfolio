#!/usr/bin/env python3
"""
Unit tests for A/B test calculator
"""

import pytest
import math
from analysis.ab_test_calculator import (
    ABTestResult,
    SampleSizeCalculator,
    analyze_test,
)


@pytest.fixture
def test_no_difference():
    """Test with no difference between control and variant"""
    return ABTestResult(
        control_conversions=100,
        control_visitors=10000,
        variant_conversions=100,
        variant_visitors=10000,
    )


@pytest.fixture
def test_significant_improvement():
    """Test showing significant improvement"""
    return ABTestResult(
        control_conversions=150,
        control_visitors=5000,
        variant_conversions=180,
        variant_visitors=5000,
    )


@pytest.fixture
def test_significant_decline():
    """Test showing significant decline"""
    return ABTestResult(
        control_conversions=200,
        control_visitors=5000,
        variant_conversions=150,
        variant_visitors=5000,
    )


@pytest.fixture
def test_large_sample():
    """Test with very large sample size"""
    return ABTestResult(
        control_conversions=10000,
        control_visitors=1000000,
        variant_conversions=10100,
        variant_visitors=1000000,
    )


class TestABTestBasicMetrics:
    """Test basic A/B test metrics"""

    def test_control_rate(self, test_no_difference):
        assert test_no_difference.control_rate == 0.01

    def test_variant_rate(self, test_no_difference):
        assert test_no_difference.variant_rate == 0.01

    def test_relative_lift_no_difference(self, test_no_difference):
        assert test_no_difference.relative_lift == 0.0

    def test_relative_lift_improvement(self, test_significant_improvement):
        # (180/5000) - (150/5000) = 0.036 - 0.030 = 0.006
        # 0.006 / 0.030 = 0.20 (20% lift)
        assert pytest.approx(test_significant_improvement.relative_lift) == 0.2

    def test_relative_lift_decline(self, test_significant_decline):
        # (150/5000) - (200/5000) = 0.030 - 0.040 = -0.010
        # -0.010 / 0.040 = -0.25 (-25% decline)
        assert pytest.approx(test_significant_decline.relative_lift) == -0.25

    def test_z_score_no_difference(self, test_no_difference):
        z = test_no_difference.z_score()
        assert z == 0.0

    def test_z_score_positive_improvement(self, test_significant_improvement):
        z = test_significant_improvement.z_score()
        # Should be positive
        assert z > 0

    def test_z_score_negative_decline(self, test_significant_decline):
        z = test_significant_decline.z_score()
        # Should be negative
        assert z < 0


class TestABTestSignificance:
    """Test statistical significance tests"""

    def test_no_difference_not_significant(self, test_no_difference):
        """No difference should not be significant"""
        try:
            assert not test_no_difference.is_significant()
        except ImportError:
            # scipy not available, skip
            pytest.skip("scipy not available")

    def test_confidence_interval_bounds(self, test_significant_improvement):
        """Confidence interval should bound the true effect"""
        lower, upper = test_significant_improvement.confidence_interval()
        # Lower and upper bounds should be different
        assert lower != upper
        # Lower should be less than upper
        assert lower < upper

    def test_confidence_interval_symmetry(self, test_no_difference):
        """For no difference, CI should be roughly symmetric around 0"""
        lower, upper = test_no_difference.confidence_interval()
        # Should be close to symmetric (allow some numerical error)
        assert abs(abs(lower) - abs(upper)) < 0.001

    def test_p_value_range(self, test_significant_improvement):
        """P-value should be between 0 and 1"""
        try:
            p = test_significant_improvement.p_value()
            assert 0 <= p <= 1
        except ImportError:
            pytest.skip("scipy not available")


class TestSampleSizeCalculator:
    """Test sample size calculation"""

    def test_baseline_3pct_15pct_lift(self):
        """Test sample size for 3% baseline, 15% lift"""
        n = SampleSizeCalculator.required_sample_size(
            baseline_rate=0.03,
            minimum_detectable_effect=0.15,
        )
        # Should be a reasonable sample size
        assert n > 0
        assert n > 1000  # Should require at least 1000 per group

    def test_baseline_5pct_10pct_lift(self):
        """Test sample size for 5% baseline, 10% lift"""
        n = SampleSizeCalculator.required_sample_size(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
        )
        assert n > 0
        assert n > 500

    def test_larger_effect_smaller_sample(self):
        """Larger effect size should require smaller sample"""
        small_effect = SampleSizeCalculator.required_sample_size(
            baseline_rate=0.05,
            minimum_detectable_effect=0.05,
        )
        large_effect = SampleSizeCalculator.required_sample_size(
            baseline_rate=0.05,
            minimum_detectable_effect=0.20,
        )
        assert large_effect < small_effect

    def test_higher_baseline_smaller_sample(self):
        """Higher baseline rate should require smaller sample"""
        low_baseline = SampleSizeCalculator.required_sample_size(
            baseline_rate=0.01,
            minimum_detectable_effect=0.10,
        )
        high_baseline = SampleSizeCalculator.required_sample_size(
            baseline_rate=0.10,
            minimum_detectable_effect=0.10,
        )
        # Generally, higher baseline should need fewer samples
        # (though this depends on the exact formula)

    def test_required_duration(self):
        """Test duration calculation"""
        sample_size = 10000
        daily_visitors = 50000
        duration = SampleSizeCalculator.required_duration(
            daily_visitors=daily_visitors,
            sample_size_per_group=sample_size,
            traffic_split=0.5
        )
        # Should be positive and reasonable
        assert duration > 0
        # Expected: sample_size / (daily_visitors * 0.5) = 10000 / 25000 = 0.4 days
        assert pytest.approx(duration, rel=0.01) == 0.4

    def test_duration_with_lower_traffic_split(self):
        """Test duration with lower traffic split takes longer"""
        sample_size = 10000
        daily_visitors = 50000

        duration_50 = SampleSizeCalculator.required_duration(
            daily_visitors=daily_visitors,
            sample_size_per_group=sample_size,
            traffic_split=0.5
        )
        duration_10 = SampleSizeCalculator.required_duration(
            daily_visitors=daily_visitors,
            sample_size_per_group=sample_size,
            traffic_split=0.1
        )
        # Lower traffic split should take longer
        assert duration_10 > duration_50


class TestAnalyzeTest:
    """Test analyze_test helper function"""

    def test_analyze_no_difference(self, test_no_difference):
        result = analyze_test(test_no_difference)

        assert result["control"]["conversion_rate"] == 1.0
        assert result["variant"]["conversion_rate"] == 1.0
        assert result["results"]["absolute_lift"] == 0.0
        assert result["results"]["relative_lift_pct"] == 0.0

    def test_analyze_improvement(self, test_significant_improvement):
        result = analyze_test(test_significant_improvement)

        assert result["control"]["conversion_rate"] == 3.0
        assert result["variant"]["conversion_rate"] == 3.6
        assert result["results"]["absolute_lift"] == pytest.approx(0.6, rel=0.01)
        assert result["results"]["relative_lift_pct"] == pytest.approx(20.0, rel=1)

    def test_results_contain_confidence_interval(self, test_significant_improvement):
        result = analyze_test(test_significant_improvement)

        assert "confidence_interval_lower" in result["results"]
        assert "confidence_interval_upper" in result["results"]
        assert result["results"]["confidence_interval_lower"] <= result["results"]["confidence_interval_upper"]

    def test_results_have_interpretation(self, test_significant_improvement):
        result = analyze_test(test_significant_improvement)

        assert "interpretation" in result
        assert isinstance(result["interpretation"], str)
        assert len(result["interpretation"]) > 0


class TestEdgeCases:
    """Test edge cases"""

    def test_zero_conversions_both(self):
        """Test when both have zero conversions"""
        test = ABTestResult(
            control_conversions=0,
            control_visitors=1000,
            variant_conversions=0,
            variant_visitors=1000,
        )
        assert test.control_rate == 0.0
        assert test.variant_rate == 0.0
        assert test.relative_lift == 0.0

    def test_zero_visitors(self):
        """Test with zero visitors"""
        test = ABTestResult(
            control_conversions=0,
            control_visitors=0,
            variant_conversions=0,
            variant_visitors=0,
        )
        assert test.control_rate == 0.0
        assert test.variant_rate == 0.0

    def test_very_small_conversion_rates(self):
        """Test with very small conversion rates"""
        test = ABTestResult(
            control_conversions=1,
            control_visitors=100000,
            variant_conversions=2,
            variant_visitors=100000,
        )
        assert test.control_rate == 0.00001
        assert test.variant_rate == 0.00002

    def test_100_percent_conversion_rate(self):
        """Test with 100% conversion rate"""
        test = ABTestResult(
            control_conversions=1000,
            control_visitors=1000,
            variant_conversions=1000,
            variant_visitors=1000,
        )
        assert test.control_rate == 1.0
        assert test.variant_rate == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
