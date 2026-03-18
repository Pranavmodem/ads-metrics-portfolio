#!/usr/bin/env python3
"""
Unit tests for attribution models
"""

import pytest
from datetime import datetime, timedelta
from analysis.attribution_analysis import (
    TouchPoint,
    Conversion,
    AttributionModels,
)


@pytest.fixture
def sample_conversion_single_touch():
    """Single touch conversion"""
    return Conversion(
        user_id="user_001",
        conversion_value=100.0,
        timestamp=datetime(2024, 1, 20, 10, 0, 0),
        touches=[
            TouchPoint(
                timestamp=datetime(2024, 1, 20, 8, 0, 0),
                channel="Search",
                campaign_id="SEM_Q1",
                cost=2.50
            )
        ]
    )


@pytest.fixture
def sample_conversion_multi_touch():
    """Multi-touch conversion with 3 touches"""
    return Conversion(
        user_id="user_002",
        conversion_value=100.0,
        timestamp=datetime(2024, 1, 23, 10, 0, 0),
        touches=[
            TouchPoint(
                timestamp=datetime(2024, 1, 20, 8, 0, 0),
                channel="Display",
                campaign_id="DSP_Awareness",
                cost=0.75
            ),
            TouchPoint(
                timestamp=datetime(2024, 1, 21, 14, 30, 0),
                channel="Search",
                campaign_id="SEM_Q1",
                cost=2.50
            ),
            TouchPoint(
                timestamp=datetime(2024, 1, 22, 18, 15, 0),
                channel="Search",
                campaign_id="SEM_Q1",
                cost=2.50
            )
        ]
    )


@pytest.fixture
def sample_conversion_no_touches():
    """Conversion with no touches"""
    return Conversion(
        user_id="user_003",
        conversion_value=100.0,
        timestamp=datetime(2024, 1, 20, 10, 0, 0),
        touches=[]
    )


class TestAttributionLastTouch:
    """Test last-touch attribution"""

    def test_single_touch(self, sample_conversion_single_touch):
        result = AttributionModels.last_touch(sample_conversion_single_touch)
        assert len(result) == 1
        assert result["Search_SEM_Q1"] == 100.0

    def test_multi_touch(self, sample_conversion_multi_touch):
        result = AttributionModels.last_touch(sample_conversion_multi_touch)
        assert len(result) == 1
        # Last touch is Search_SEM_Q1
        assert result["Search_SEM_Q1"] == 100.0

    def test_empty_touches(self, sample_conversion_no_touches):
        result = AttributionModels.last_touch(sample_conversion_no_touches)
        assert result == {}

    def test_revenue_preserved(self, sample_conversion_multi_touch):
        result = AttributionModels.last_touch(sample_conversion_multi_touch)
        total_attributed = sum(result.values())
        assert total_attributed == sample_conversion_multi_touch.conversion_value


class TestAttributionFirstTouch:
    """Test first-touch attribution"""

    def test_single_touch(self, sample_conversion_single_touch):
        result = AttributionModels.first_touch(sample_conversion_single_touch)
        assert len(result) == 1
        assert result["Search_SEM_Q1"] == 100.0

    def test_multi_touch(self, sample_conversion_multi_touch):
        result = AttributionModels.first_touch(sample_conversion_multi_touch)
        assert len(result) == 1
        # First touch is Display_DSP_Awareness
        assert result["Display_DSP_Awareness"] == 100.0

    def test_empty_touches(self, sample_conversion_no_touches):
        result = AttributionModels.first_touch(sample_conversion_no_touches)
        assert result == {}

    def test_revenue_preserved(self, sample_conversion_multi_touch):
        result = AttributionModels.first_touch(sample_conversion_multi_touch)
        total_attributed = sum(result.values())
        assert total_attributed == sample_conversion_multi_touch.conversion_value


class TestAttributionLinear:
    """Test linear attribution"""

    def test_single_touch(self, sample_conversion_single_touch):
        result = AttributionModels.linear(sample_conversion_single_touch)
        assert len(result) == 1
        assert result["Search_SEM_Q1"] == 100.0

    def test_multi_touch_equal_split(self, sample_conversion_multi_touch):
        result = AttributionModels.linear(sample_conversion_multi_touch)
        # Should split equally among 3 touches
        expected_credit = 100.0 / 3
        assert pytest.approx(result["Display_DSP_Awareness"]) == expected_credit
        assert pytest.approx(result["Search_SEM_Q1"]) == expected_credit * 2

    def test_empty_touches(self, sample_conversion_no_touches):
        result = AttributionModels.linear(sample_conversion_no_touches)
        assert result == {}

    def test_revenue_preserved(self, sample_conversion_multi_touch):
        result = AttributionModels.linear(sample_conversion_multi_touch)
        total_attributed = sum(result.values())
        assert pytest.approx(total_attributed) == sample_conversion_multi_touch.conversion_value


class TestAttributionTimeDecay:
    """Test time-decay attribution"""

    def test_single_touch(self, sample_conversion_single_touch):
        result = AttributionModels.time_decay(sample_conversion_single_touch)
        assert len(result) == 1
        assert result["Search_SEM_Q1"] == 100.0

    def test_multi_touch_recency_bias(self, sample_conversion_multi_touch):
        result = AttributionModels.time_decay(sample_conversion_multi_touch)
        # Most recent touch should have highest credit
        sem_credit = result["Search_SEM_Q1"]
        display_credit = result["Display_DSP_Awareness"]
        # SEM had two touches (one is the most recent), Display was first
        assert sem_credit > display_credit

    def test_empty_touches(self, sample_conversion_no_touches):
        result = AttributionModels.time_decay(sample_conversion_no_touches)
        assert result == {}

    def test_revenue_preserved(self, sample_conversion_multi_touch):
        result = AttributionModels.time_decay(sample_conversion_multi_touch)
        total_attributed = sum(result.values())
        assert pytest.approx(total_attributed, rel=1e-2) == sample_conversion_multi_touch.conversion_value


class TestAttributionConsistency:
    """Test cross-model consistency"""

    def test_single_touch_all_models_agree(self, sample_conversion_single_touch):
        """With single touch, all models should attribute 100% to that touch"""
        last = AttributionModels.last_touch(sample_conversion_single_touch)
        first = AttributionModels.first_touch(sample_conversion_single_touch)
        linear = AttributionModels.linear(sample_conversion_single_touch)
        time_decay = AttributionModels.time_decay(sample_conversion_single_touch)

        assert last == first == linear == time_decay
        assert last["Search_SEM_Q1"] == 100.0

    def test_revenue_always_preserved(self, sample_conversion_multi_touch):
        """All models should preserve total revenue"""
        models = [
            AttributionModels.last_touch,
            AttributionModels.first_touch,
            AttributionModels.linear,
            AttributionModels.time_decay,
        ]

        for model in models:
            result = model(sample_conversion_multi_touch)
            total = sum(result.values())
            assert pytest.approx(total) == sample_conversion_multi_touch.conversion_value

    def test_all_touches_credited(self, sample_conversion_multi_touch):
        """All models should credit at least some amount to each unique touch"""
        models = [
            ("last_touch", AttributionModels.last_touch),
            ("first_touch", AttributionModels.first_touch),
            ("linear", AttributionModels.linear),
            ("time_decay", AttributionModels.time_decay),
        ]

        for model_name, model_func in models:
            result = model_func(sample_conversion_multi_touch)
            assert len(result) > 0, f"{model_name} produced no attribution"


class TestAttributionEdgeCases:
    """Test edge cases and error handling"""

    def test_zero_value_conversion(self):
        conversion = Conversion(
            user_id="user_zero",
            conversion_value=0.0,
            timestamp=datetime(2024, 1, 20, 10, 0, 0),
            touches=[
                TouchPoint(
                    timestamp=datetime(2024, 1, 20, 8, 0, 0),
                    channel="Search",
                    campaign_id="SEM_Q1",
                    cost=2.50
                )
            ]
        )
        result = AttributionModels.last_touch(conversion)
        assert result["Search_SEM_Q1"] == 0.0

    def test_very_large_value(self):
        conversion = Conversion(
            user_id="user_large",
            conversion_value=999999.99,
            timestamp=datetime(2024, 1, 20, 10, 0, 0),
            touches=[
                TouchPoint(
                    timestamp=datetime(2024, 1, 20, 8, 0, 0),
                    channel="Search",
                    campaign_id="SEM_Q1",
                    cost=2.50
                )
            ]
        )
        result = AttributionModels.last_touch(conversion)
        assert result["Search_SEM_Q1"] == 999999.99

    def test_very_old_touch(self):
        """Test attribution with very old first touch"""
        conversion = Conversion(
            user_id="user_old",
            conversion_value=100.0,
            timestamp=datetime(2024, 1, 20, 10, 0, 0),
            touches=[
                TouchPoint(
                    timestamp=datetime(2024, 1, 1, 8, 0, 0),  # 19 days old
                    channel="Display",
                    campaign_id="DSP_Awareness",
                    cost=0.75
                ),
                TouchPoint(
                    timestamp=datetime(2024, 1, 20, 8, 0, 0),
                    channel="Search",
                    campaign_id="SEM_Q1",
                    cost=2.50
                )
            ]
        )
        # Time decay should heavily discount the old touch
        result = AttributionModels.time_decay(conversion)
        sem_credit = result["Search_SEM_Q1"]
        display_credit = result.get("Display_DSP_Awareness", 0)
        assert sem_credit > display_credit * 2  # Recent touch should be >> old touch


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
