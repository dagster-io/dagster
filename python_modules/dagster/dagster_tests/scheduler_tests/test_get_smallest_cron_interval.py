import datetime
from unittest.mock import patch

import pytest
from dagster._core.test_utils import freeze_time
from dagster._utils.schedules import (
    _get_smallest_cron_interval_with_sampling,
    get_smallest_cron_interval,
)
from dagster_shared.check import CheckError

# ==============================================================================
# Test 1: Invalid cron strings
# ==============================================================================


def test_invalid_cron_string():
    """Test that invalid cron strings raise CheckError."""
    match_str = "must be a valid cron string"
    with pytest.raises(CheckError, match=match_str):
        get_smallest_cron_interval("invalid cron")
    with pytest.raises(CheckError, match=match_str):
        get_smallest_cron_interval("* * * *")  # Only 4 fields
    with pytest.raises(CheckError, match=match_str):
        get_smallest_cron_interval("60 * * * *")  # Invalid minute
    with pytest.raises(CheckError, match=match_str):
        get_smallest_cron_interval("0 0 32 * *")  # Invalid day
    with pytest.raises(CheckError, match=match_str):
        get_smallest_cron_interval("* * * * * *")  # More than 5 fields


# ==============================================================================
# Test 2: nth_weekday_of_month patterns (fall back to sampling)
# ==============================================================================


def test_nth_weekday_of_month_fallback():
    """Test that nth weekday patterns fall back to sampling."""
    # First Monday of the month
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(days=28)
        result = get_smallest_cron_interval("0 0 * * MON#1")
        # Verify that the sampling-based method was called
        mock_sampling.assert_called_once_with("0 0 * * MON#1", None)
        # Verify the result is what the sampling method returned
        assert result == datetime.timedelta(days=28)


# ==============================================================================
# Test 3: Both day-of-month AND day-of-week constrained (fall back to sampling)
# ==============================================================================


def test_both_day_constraints_fallback():
    """Test that patterns with both day-of-month and day-of-week fall back to sampling."""
    # 15th of month AND Mondays (uses OR logic in cron)
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(days=1)
        result = get_smallest_cron_interval("0 0 15 * 1")
        # Verify that the sampling-based method was called
        mock_sampling.assert_called_once_with("0 0 15 * 1", None)
        assert result == datetime.timedelta(days=1)

    # Another example: 1st and 15th of month AND weekends
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(days=1)
        result = get_smallest_cron_interval("0 0 1,15 * 0,6")
        mock_sampling.assert_called_once_with("0 0 1,15 * 0,6", None)
        assert result == datetime.timedelta(days=1)


# ==============================================================================
# Test 4: Minutes wildcarded (returns 1 minute)
# ==============================================================================


def test_minutes_wildcarded():
    """Test patterns with wildcarded minutes return 1 minute interval."""
    # Every minute
    assert get_smallest_cron_interval("* * * * *") == datetime.timedelta(minutes=1)

    # Every minute during specific hours
    assert get_smallest_cron_interval("* */10 * * */4") == datetime.timedelta(minutes=1)

    # Every minute during hour 0
    assert get_smallest_cron_interval("* 0 * * *") == datetime.timedelta(minutes=1)

    # Every minute on Mondays
    assert get_smallest_cron_interval("* * * * 1") == datetime.timedelta(minutes=1)


# ==============================================================================
# Test 5: Multiple minute values
# ==============================================================================


def test_multiple_minutes_all_wildcarded():
    """Test multiple minute values with all other fields wildcarded."""
    # Every 15 minutes
    assert get_smallest_cron_interval("0,15,30,45 * * * *") == datetime.timedelta(minutes=15)

    # Every 5 minutes
    assert get_smallest_cron_interval("0,5,10 * * * *") == datetime.timedelta(minutes=5)

    # Every 10 minutes
    assert get_smallest_cron_interval("0,10,20,30 * * * *") == datetime.timedelta(minutes=10)

    # Irregular intervals - should return minimum gap
    assert get_smallest_cron_interval("0,5,15 * * * *") == datetime.timedelta(minutes=5)


def test_multiple_minutes_with_constraints_fallback():
    """Test multiple minute values with other constraints fall back to sampling."""
    # Multiple minutes with hour constraint
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(minutes=30)
        result = get_smallest_cron_interval("0,30 0,12 * * *")
        # Verify that the sampling-based method was called
        mock_sampling.assert_called_once_with("0,30 0,12 * * *", None)
        assert result == datetime.timedelta(minutes=30)

    # Multiple minutes with day-of-week constraint
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(minutes=15)
        result = get_smallest_cron_interval("0,15,30 * * * 1")
        mock_sampling.assert_called_once_with("0,15,30 * * * 1", None)
        assert result == datetime.timedelta(minutes=15)

    # Multiple minutes with month constraint
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(minutes=30)
        result = get_smallest_cron_interval("0,30 * * 6 *")
        mock_sampling.assert_called_once_with("0,30 * * 6 *", None)
        assert result == datetime.timedelta(minutes=30)


# ==============================================================================
# Test 6: Single minute value + hours wildcarded
# ==============================================================================


def test_single_minute_hours_wildcarded_all_other_wildcarded():
    """Test single minute with wildcarded hours and all other fields wildcarded."""
    # Every hour at minute 0
    assert get_smallest_cron_interval("0 * * * *") == datetime.timedelta(hours=1)

    # Every hour at minute 15
    assert get_smallest_cron_interval("15 * * * *") == datetime.timedelta(hours=1)

    # Every hour at minute 30
    assert get_smallest_cron_interval("30 * * * *") == datetime.timedelta(hours=1)


def test_single_minute_hours_wildcarded_with_constraints_fallback():
    """Test single minute with wildcarded hours but other constraints fall back to sampling."""
    # Single minute, wildcard hours, but constrained to Mondays
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(hours=1)
        result = get_smallest_cron_interval("0 * * * 1")
        mock_sampling.assert_called_once_with("0 * * * 1", None)
        assert result == datetime.timedelta(hours=1)

    # Single minute, wildcard hours, but constrained to 15th of month
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(hours=1)
        result = get_smallest_cron_interval("0 * 15 * *")
        mock_sampling.assert_called_once_with("0 * 15 * *", None)
        assert result == datetime.timedelta(hours=1)

    # Single minute, wildcard hours, but constrained to June
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(hours=1)
        result = get_smallest_cron_interval("0 * * 6 *")
        mock_sampling.assert_called_once_with("0 * * 6 *", None)
        assert result == datetime.timedelta(hours=1)


# ==============================================================================
# Test 7: Single minute + multiple hour values
# ==============================================================================


def test_single_minute_multiple_hours_all_wildcarded():
    """Test single minute with multiple hours and all other fields wildcarded."""
    # Every 2 hours
    assert get_smallest_cron_interval("0 */2 * * *") == datetime.timedelta(hours=2)

    # Every 6 hours
    assert get_smallest_cron_interval("0 0,6,12,18 * * *") == datetime.timedelta(hours=6)

    # Every 4 hours
    assert get_smallest_cron_interval("0 0,4,8,12,16,20 * * *") == datetime.timedelta(hours=4)

    # Irregular hour intervals - minimum gap
    assert get_smallest_cron_interval("0 0,3,6 * * *") == datetime.timedelta(hours=3)


def test_single_minute_multiple_hours_with_constraints_fallback():
    """Test single minute with multiple hours but other constraints fall back to sampling."""
    # Multiple hours with day-of-week constraint
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(hours=12)
        result = get_smallest_cron_interval("0 0,12 * * 1")
        mock_sampling.assert_called_once_with("0 0,12 * * 1", None)
        assert result == datetime.timedelta(hours=12)

    # Multiple hours with day-of-month constraint
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(hours=6)
        result = get_smallest_cron_interval("0 0,6,12 15 * *")
        mock_sampling.assert_called_once_with("0 0,6,12 15 * *", None)
        assert result == datetime.timedelta(hours=6)


# ==============================================================================
# Test 8: Single minute + single hour (daily/weekly/monthly patterns)
# ==============================================================================


def test_daily_pattern():
    """Test daily patterns (single minute, single hour, all days)."""
    # Daily at midnight
    assert get_smallest_cron_interval("0 0 * * *") == datetime.timedelta(days=1)

    # Daily at 3:30 AM
    assert get_smallest_cron_interval("30 3 * * *") == datetime.timedelta(days=1)

    # Daily at noon
    assert get_smallest_cron_interval("0 12 * * *") == datetime.timedelta(days=1)


def test_weekly_single_day():
    """Test weekly patterns with a single day of week."""
    # Weekly on Monday
    assert get_smallest_cron_interval("0 0 * * 1") == datetime.timedelta(days=7)

    # Weekly on Sunday
    assert get_smallest_cron_interval("0 0 * * 0") == datetime.timedelta(days=7)

    # Weekly on Friday at 5 PM
    assert get_smallest_cron_interval("0 17 * * 5") == datetime.timedelta(days=7)


def test_weekly_multiple_days():
    """Test weekly patterns with multiple days of week."""
    # Mon, Wed, Fri (minimum gap is 2 days)
    assert get_smallest_cron_interval("0 0 * * 1,3,5") == datetime.timedelta(days=2)

    # Sun, Tue, Thu, Sat (gaps: 0->2=2, 2->4=2, 4->6=2, 6->0(wrap)=1, min=1)
    assert get_smallest_cron_interval("0 0 * * 0,2,4,6") == datetime.timedelta(days=1)

    # Mon and Thu (minimum gap is 3 days)
    assert get_smallest_cron_interval("0 0 * * 1,4") == datetime.timedelta(days=3)


def test_monthly_pattern_fallback():
    """Test monthly patterns fall back to sampling."""
    # 1st of every month
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(days=28)
        result = get_smallest_cron_interval("0 0 1 * *")
        # Verify that the sampling-based method was called
        mock_sampling.assert_called_once_with("0 0 1 * *", None)
        assert result == datetime.timedelta(days=28)

    # 15th of every month
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(days=28)
        result = get_smallest_cron_interval("0 0 15 * *")
        mock_sampling.assert_called_once_with("0 0 15 * *", None)
        assert result == datetime.timedelta(days=28)


def test_month_constrained_fallback():
    """Test patterns with month constraints fall back to sampling."""
    # Every day in June
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(days=1)
        result = get_smallest_cron_interval("0 0 * 6 *")
        mock_sampling.assert_called_once_with("0 0 * 6 *", None)
        assert result == datetime.timedelta(days=1)

    # Every Monday in January and July
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(days=7)
        result = get_smallest_cron_interval("0 0 * 1,7 1")
        mock_sampling.assert_called_once_with("0 0 * 1,7 1", None)
        assert result == datetime.timedelta(days=7)


# ==============================================================================
# Test 9: Edge cases and wrap-arounds
# ==============================================================================


def test_wrap_around_minutes():
    """Test that minute gaps wrap around correctly (e.g., 50->5 is 15 min, not 45)."""
    # 50, 5, 20 -> gaps are: 5-50=15 (wrap), 20-5=15, 50-20=30 -> min is 15
    assert get_smallest_cron_interval("50,5,20 * * * *") == datetime.timedelta(minutes=15)

    # 55, 5 -> gap is 5-55=10 (wrap around midnight)
    assert get_smallest_cron_interval("55,5 * * * *") == datetime.timedelta(minutes=10)

    # 0, 59 -> gap is 1 minute (wrap)
    assert get_smallest_cron_interval("0,59 * * * *") == datetime.timedelta(minutes=1)


def test_wrap_around_hours():
    """Test that hour gaps wrap around correctly."""
    # 22, 2 -> gap is 2-22=4 (wrap around midnight)
    assert get_smallest_cron_interval("0 22,2 * * *") == datetime.timedelta(hours=4)

    # 20, 4, 12 -> gaps are: 4-20=8 (wrap), 12-4=8, 20-12=8 -> min is 8
    assert get_smallest_cron_interval("0 20,4,12 * * *") == datetime.timedelta(hours=8)


def test_wrap_around_days_of_week():
    """Test that day-of-week gaps wrap around correctly."""
    # Saturday (6) and Monday (1) -> gap is 1-6=2 (wrap: Sat->Sun->Mon)
    assert get_smallest_cron_interval("0 0 * * 6,1") == datetime.timedelta(days=2)

    # Sunday (0) and Friday (5) -> gap is 5-0=5, 0-5=2 (wrap: Fri->Sat->Sun) -> min is 2
    assert get_smallest_cron_interval("0 0 * * 0,5") == datetime.timedelta(days=2)

    # Thursday (4) and Sunday (0) -> gap is 0-4=3 (wrap: Thu->Fri->Sat->Sun)
    # But also 4-0=4 going forward
    assert get_smallest_cron_interval("0 0 * * 4,0") == datetime.timedelta(days=3)


def test_execution_timezone_parameter():
    """Test that execution_timezone parameter is passed to fallback function."""
    # Test with a pattern that falls back to sampling
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(days=28)
        result_utc = get_smallest_cron_interval("0 0 1 * *", "UTC")
        # Verify that the sampling-based method was called with the correct timezone
        mock_sampling.assert_called_once_with("0 0 1 * *", "UTC")
        assert result_utc == datetime.timedelta(days=28)

    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(days=28)
        result_berlin = get_smallest_cron_interval("0 0 1 * *", "Europe/Berlin")
        # Verify that the sampling-based method was called with the correct timezone
        mock_sampling.assert_called_once_with("0 0 1 * *", "Europe/Berlin")
        assert result_berlin == datetime.timedelta(days=28)


def test_step_patterns():
    """Test cron step patterns (*/N)."""
    # Every 1 minute
    assert get_smallest_cron_interval("*/1 * * * *") == datetime.timedelta(minutes=1)

    # Every 5 minutes
    assert get_smallest_cron_interval("*/5 * * * *") == datetime.timedelta(minutes=5)

    # Every 10 minutes
    assert get_smallest_cron_interval("*/10 * * * *") == datetime.timedelta(minutes=10)

    # Every 15 minutes
    assert get_smallest_cron_interval("*/15 * * * *") == datetime.timedelta(minutes=15)

    # Every 20 minutes
    assert get_smallest_cron_interval("*/20 * * * *") == datetime.timedelta(minutes=20)

    # Every 30 minutes
    assert get_smallest_cron_interval("*/30 * * * *") == datetime.timedelta(minutes=30)


def test_range_patterns():
    """Test cron range patterns (A-B)."""
    # Minutes 0-30 every hour (should analyze as multiple values)
    result = get_smallest_cron_interval("0-30 * * * *")
    # This expands to 0,1,2,...,30 so minimum gap is 1
    assert result == datetime.timedelta(minutes=1)

    # Hours 9-17 (business hours) - expands to 9,10,11,12,13,14,15,16,17
    result = get_smallest_cron_interval("0 9-17 * * *")
    assert result == datetime.timedelta(hours=1)


def test_single_value_patterns():
    """Test patterns with single specific values (not wildcarded)."""
    # Single minute value (not wildcard, but len==1)
    assert get_smallest_cron_interval("5 * * * *") == datetime.timedelta(hours=1)

    # Single hour value
    assert get_smallest_cron_interval("0 5 * * *") == datetime.timedelta(days=1)


def test_complex_patterns_fallback():
    """Test that complex patterns fall back to sampling appropriately."""
    # Pattern with no clear deterministic interval
    with patch(
        "dagster._utils.schedules._get_smallest_cron_interval_with_sampling"
    ) as mock_sampling:
        mock_sampling.return_value = datetime.timedelta(hours=3)
        result = get_smallest_cron_interval("0,30 */3 */2 * *")
        mock_sampling.assert_called_once_with("0,30 */3 */2 * *", None)
        assert result == datetime.timedelta(hours=3)


# ==============================================================================
# Test 10: Comprehensive integration tests
# ==============================================================================


def test_common_real_world_patterns():
    """Test common real-world cron patterns not covered by other tests."""
    # Every 4 hours (not in comparison tests)
    assert get_smallest_cron_interval("0 */4 * * *") == datetime.timedelta(hours=4)

    # Twice daily (midnight and noon) (not in comparison tests)
    assert get_smallest_cron_interval("0 0,12 * * *") == datetime.timedelta(hours=12)

    # Daily at 2 AM (not in comparison tests)
    assert get_smallest_cron_interval("0 2 * * *") == datetime.timedelta(days=1)


def test_comparison_with_sampling():
    """Test that deterministic results match sampling-based results for known patterns."""
    test_patterns = [
        # Basic minute intervals
        "* * * * *",
        "*/5 * * * *",
        "*/15 * * * *",
        "*/30 * * * *",
        "0,15,30,45 * * * *",
        # Hourly intervals
        "0 * * * *",
        "0 */2 * * *",
        "0 */6 * * *",
        "0 */12 * * *",
        # Daily intervals
        "0 0 * * *",
        "30 14 * * *",
        # Weekly intervals
        "0 0 * * 0",
        "0 9 * * 1",
        "0 0 * * 1,3,5",
        # Irregular schedules
        "15,45 * * * *",
        "0 9,17 * * *",
        "0 9 * * 1-5",
        "0 9 * * 1,3,5",
    ]

    for pattern in test_patterns:
        deterministic = get_smallest_cron_interval(pattern)
        sampling = _get_smallest_cron_interval_with_sampling(pattern)
        assert deterministic == sampling, f"Mismatch for pattern {pattern}"


def test_comparison_with_sampling_monthly():
    """Test that monthly patterns match between deterministic and sampling methods."""
    # Monthly patterns fall back to sampling in the deterministic implementation
    monthly_patterns = [
        "0 0 1 * *",  # 1st of every month
        "0 12 15 * *",  # 15th of every month
    ]

    for pattern in monthly_patterns:
        deterministic = get_smallest_cron_interval(pattern)
        sampling = _get_smallest_cron_interval_with_sampling(pattern)
        assert deterministic == sampling, f"Mismatch for pattern {pattern}"
        # Both should return 28 days (shortest month)
        assert deterministic == datetime.timedelta(days=28)


def test_comparison_with_sampling_leap_year():
    """Test leap year patterns match between methods."""
    pattern = "0 0 29 2 *"  # Feb 29th only
    deterministic = get_smallest_cron_interval(pattern)
    sampling = _get_smallest_cron_interval_with_sampling(pattern)
    assert deterministic == sampling, f"Mismatch for pattern {pattern}"
    # Should be at least 1 year
    assert deterministic.days >= 365


# ==============================================================================
# Test 12: _get_smallest_gap helper function tests
# ==============================================================================


def test_get_smallest_gap_two_values():
    """Test _get_smallest_gap with exactly two values."""
    from dagster._utils.schedules import _get_smallest_gap

    # Simple case: [5, 10] -> gap is 5
    assert _get_smallest_gap([5, 10]) == 5

    # Reverse order (should still work due to sorting): [10, 5] -> gap is 5
    assert _get_smallest_gap([10, 5]) == 5

    # Large gap: [0, 50] -> gap is 50
    assert _get_smallest_gap([0, 50]) == 50


def test_get_smallest_gap_multiple_values():
    """Test _get_smallest_gap with multiple values."""
    from dagster._utils.schedules import _get_smallest_gap

    # Three values: [0, 15, 30] -> gaps are 15, 15 -> min is 15
    assert _get_smallest_gap([0, 15, 30]) == 15

    # Irregular gaps: [0, 5, 15] -> gaps are 5, 10 -> min is 5
    assert _get_smallest_gap([0, 5, 15]) == 5

    # Gaps at the end: [0, 10, 20, 25] -> gaps are 10, 10, 5 -> min is 5
    assert _get_smallest_gap([0, 10, 20, 25]) == 5

    # Unsorted input: [30, 0, 15] -> sorted to [0, 15, 30] -> gaps are 15, 15 -> min is 15
    assert _get_smallest_gap([30, 0, 15]) == 15


def test_get_smallest_gap_with_wrap_around():
    """Test _get_smallest_gap with wrap-around at specified boundary."""
    from dagster._utils.schedules import _get_smallest_gap

    # Wrap-around for minutes: [50, 5, 20] with wrap_at=60
    # Sorted: [5, 20, 50]
    # Gaps: 20-5=15, 50-20=30, wrap: (60-50)+5=15
    # Min: 15
    assert _get_smallest_gap([50, 5, 20], wrap_at=60) == 15

    # Wrap-around for minutes: [55, 5] with wrap_at=60
    # Gaps: 5-55 wrap = (60-55)+5=10
    assert _get_smallest_gap([55, 5], wrap_at=60) == 10

    # Wrap-around for minutes: [0, 59] with wrap_at=60
    # Sorted: [0, 59]
    # Gaps: 59-0=59, wrap: (60-59)+0=1
    # Min: 1
    assert _get_smallest_gap([0, 59], wrap_at=60) == 1

    # Wrap-around for hours: [22, 2] with wrap_at=24
    # Sorted: [2, 22]
    # Gaps: 22-2=20, wrap: (24-22)+2=4
    # Min: 4
    assert _get_smallest_gap([22, 2], wrap_at=24) == 4

    # Wrap-around for hours: [20, 4, 12] with wrap_at=24
    # Sorted: [4, 12, 20]
    # Gaps: 12-4=8, 20-12=8, wrap: (24-20)+4=8
    # Min: 8
    assert _get_smallest_gap([20, 4, 12], wrap_at=24) == 8

    # Wrap-around for days of week: [6, 1] with wrap_at=7 (Saturday to Monday)
    # Sorted: [1, 6]
    # Gaps: 6-1=5, wrap: (7-6)+1=2
    # Min: 2
    assert _get_smallest_gap([6, 1], wrap_at=7) == 2

    # Wrap-around for days of week: [0, 5] with wrap_at=7 (Sunday and Friday)
    # Sorted: [0, 5]
    # Gaps: 5-0=5, wrap: (7-5)+0=2
    # Min: 2
    assert _get_smallest_gap([0, 5], wrap_at=7) == 2

    # Wrap-around for days of week: [4, 0] with wrap_at=7 (Thursday and Sunday)
    # Sorted: [0, 4]
    # Gaps: 4-0=4, wrap: (7-4)+0=3
    # Min: 3
    assert _get_smallest_gap([4, 0], wrap_at=7) == 3


def test_get_smallest_gap_edge_cases():
    """Test _get_smallest_gap with edge cases."""
    from dagster._utils.schedules import _get_smallest_gap

    # Single value: returns None (no gaps possible)
    assert _get_smallest_gap([5]) is None

    # Empty list: returns None
    assert _get_smallest_gap([]) is None

    # Consecutive integers: [0, 1, 2, 3] -> all gaps are 1
    assert _get_smallest_gap([0, 1, 2, 3]) == 1

    # All same value (after sorting duplicate scenario): [5, 5] -> gap is 0
    assert _get_smallest_gap([5, 5]) == 0


def test_get_smallest_gap_wrap_around_equal_to_non_wrap():
    """Test cases where wrap-around gap equals non-wrap gap."""
    from dagster._utils.schedules import _get_smallest_gap

    # [0, 30] with wrap_at=60
    # Gaps: 30-0=30, wrap: (60-30)+0=30
    # Min: 30
    assert _get_smallest_gap([0, 30], wrap_at=60) == 30

    # [0, 12] with wrap_at=24
    # Gaps: 12-0=12, wrap: (24-12)+0=12
    # Min: 12
    assert _get_smallest_gap([0, 12], wrap_at=24) == 12


def test_get_smallest_gap_real_world_cron_scenarios():
    """Test _get_smallest_gap with real-world cron schedule scenarios."""
    from dagster._utils.schedules import _get_smallest_gap

    # Every 15 minutes: 0, 15, 30, 45
    assert _get_smallest_gap([0, 15, 30, 45], wrap_at=60) == 15

    # Every 5 minutes: 0, 5, 10, 15, 20, ...
    assert _get_smallest_gap([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55], wrap_at=60) == 5

    # Business hours (9 AM to 5 PM): 9, 10, 11, 12, 13, 14, 15, 16, 17
    assert _get_smallest_gap([9, 10, 11, 12, 13, 14, 15, 16, 17]) == 1

    # Twice daily: midnight and noon [0, 12]
    assert _get_smallest_gap([0, 12], wrap_at=24) == 12

    # Weekdays: Mon(1), Tue(2), Wed(3), Thu(4), Fri(5)
    # Gaps: all 1, but wrap from Fri to Mon is (7-5)+1 = 3
    assert _get_smallest_gap([1, 2, 3, 4, 5], wrap_at=7) == 1

    # Mon, Wed, Fri: 1, 3, 5
    # Gaps: 3-1=2, 5-3=2, wrap: (7-5)+1=3
    assert _get_smallest_gap([1, 3, 5], wrap_at=7) == 2

    # Weekend: Sat(6), Sun(0)
    # Sorted: [0, 6]
    # Gaps: 6-0=6, wrap: (7-6)+0=1
    assert _get_smallest_gap([0, 6], wrap_at=7) == 1


def test_comparison_with_sampling_complex_patterns():
    """Test complex patterns match between methods."""
    complex_patterns = [
        "*/5 9-17 * * 1-5",  # Every 5 minutes during business hours on weekdays
        "0,30 8,12,16 * * 1-5",  # Multiple times during specific hours on weekdays
        "0 9 1,15 * *",  # 1st and 15th of month
    ]

    for pattern in complex_patterns:
        deterministic = get_smallest_cron_interval(pattern)
        sampling = _get_smallest_cron_interval_with_sampling(pattern)
        assert deterministic == sampling, f"Mismatch for pattern {pattern}"


def test_comparison_with_sampling_timezones():
    """Test that timezone handling matches between methods."""
    pattern = "0 * * * *"  # Hourly
    timezones = ["UTC", "America/New_York", "Europe/Berlin", "Asia/Tokyo"]

    for tz in timezones:
        deterministic = get_smallest_cron_interval(pattern, tz)
        sampling = _get_smallest_cron_interval_with_sampling(pattern, tz)
        assert deterministic == sampling, f"Mismatch for pattern {pattern} in timezone {tz}"
        assert deterministic == datetime.timedelta(hours=1)


# ==============================================================================
# Test 11: Sampling-specific tests (DST, variable intervals)
# ==============================================================================


def test_sampling_dst_transitions():
    """Test DST transition edge cases with sampling method.

    The deterministic method cannot detect DST transitions, so this test validates
    that the sampling-based method correctly handles both spring forward (23-hour intervals)
    and fall back (negative intervals that should be skipped) DST transitions.

    We freeze time to ensure the sampling period will cross DST transitions.
    """
    # Test spring forward (clocks jump ahead 1 hour, creating 23-hour intervals)
    # Freeze time to February 2024, so that sampling from a year ago (Feb 2023)
    # will cross the March 2024 spring forward DST transition
    freeze_datetime_spring = datetime.datetime(2024, 2, 15, 12, 0, 0)
    with freeze_time(freeze_datetime_spring):
        # Daily at 2am in America/New_York - should catch the 23-hour interval during spring forward
        # The spring forward happens on March 10, 2024 at 2:00 AM -> 3:00 AM
        interval = _get_smallest_cron_interval_with_sampling("0 2 * * *", "America/New_York")
        assert interval == datetime.timedelta(hours=23)

        # Hourly schedule should not be affected by DST for minimum interval
        interval = _get_smallest_cron_interval_with_sampling("0 * * * *", "America/New_York")
        assert interval == datetime.timedelta(hours=1)

    # Test fall back (clocks go back 1 hour, creating negative intervals that should be skipped)
    # Freeze time to September 2024, so that sampling from a year ago (Sep 2023)
    # will cross the November 2024 fall back DST transition
    freeze_datetime_fall = datetime.datetime(2024, 9, 15, 12, 0, 0)
    with freeze_time(freeze_datetime_fall):
        # Daily at 2am in America/New_York during fall back
        # The fall back happens on November 3, 2024 at 2:00 AM -> 1:00 AM
        # Should still return 23 hours as minimum (not negative intervals)
        interval = _get_smallest_cron_interval_with_sampling("0 2 * * *", "America/New_York")
        assert interval == datetime.timedelta(hours=23)

    # Test Europe/Berlin DST transitions
    with freeze_time(freeze_datetime_spring):
        # Different timezone with DST (Europe/Berlin)
        # Spring forward happens on March 31, 2024 at 2:00 AM -> 3:00 AM
        interval = _get_smallest_cron_interval_with_sampling("0 2 * * *", "Europe/Berlin")
        assert interval == datetime.timedelta(hours=23)

    with freeze_time(freeze_datetime_fall):
        # Fall back happens on October 27, 2024 at 3:00 AM -> 2:00 AM
        interval = _get_smallest_cron_interval_with_sampling("0 2 * * *", "Europe/Berlin")
        assert interval == datetime.timedelta(hours=23)


def test_sampling_negative_interval_handling():
    """Test that negative intervals during DST fall-back are properly skipped.

    During a fall-back DST transition, the cron iterator may produce timestamps
    that appear to go backward in wall-clock time. This test ensures that these
    negative intervals are skipped and don't affect the minimum interval calculation.
    """
    # Use a time just before the fall DST transition to maximize chances of hitting
    # the negative interval code path. We use hourly schedule which emits both
    # PRE_TRANSITION and POST_TRANSITION times during the ambiguous hour.
    freeze_datetime = datetime.datetime(2024, 11, 2, 12, 0, 0)
    with freeze_time(freeze_datetime):
        # Hourly schedule in America/New_York during fall back (Nov 3, 2024 at 2:00 AM -> 1:00 AM)
        # The hourly schedule will emit times during the ambiguous hour twice (fold=0 and fold=1)
        # which can create situations where wall-clock times appear to go backward
        interval = _get_smallest_cron_interval_with_sampling("0 * * * *", "America/New_York")
        # Should still return 1 hour as minimum, not negative intervals
        assert interval == datetime.timedelta(hours=1)

    # Test with a different pattern that might expose negative intervals
    freeze_datetime = datetime.datetime(2024, 11, 2, 12, 0, 0)
    with freeze_time(freeze_datetime):
        # Every 30 minutes during the fall back transition
        interval = _get_smallest_cron_interval_with_sampling("0,30 * * * *", "America/New_York")
        # Should return 30 minutes, not negative intervals
        assert interval == datetime.timedelta(minutes=30)


def test_sampling_zero_interval_with_mock():
    """Test the error handling for genuine zero intervals (should not happen in practice).

    This test uses mocking to force a scenario where a zero interval occurs without
    being a DST transition, which should raise an exception.
    """
    from unittest.mock import patch

    with patch("dagster._utils.schedules.schedule_execution_time_iterator") as mock_iter:
        # Create a mock iterator that returns two ticks with the same timestamp
        # but WITHOUT different fold values (not a DST transition)
        base_time = datetime.datetime(2024, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        same_time = datetime.datetime(2024, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)

        mock_iter.return_value = iter([base_time, same_time])

        # This should raise an exception for genuine zero interval
        with pytest.raises(Exception, match="Encountered a genuine zero interval"):
            _get_smallest_cron_interval_with_sampling("0 * * * *", "UTC")


def test_sampling_stop_iteration_with_mock():
    """Test the StopIteration exception handling (should not happen with cron iterators).

    This test uses mocking to force a StopIteration exception from the iterator,
    which should be caught and handled gracefully.
    """
    from unittest.mock import patch

    with patch("dagster._utils.schedules.schedule_execution_time_iterator") as mock_iter:
        # Create a mock iterator that immediately raises StopIteration
        base_time = datetime.datetime(2024, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        mock_iter.return_value = iter([base_time])  # Only one tick, then stops

        # This should handle the StopIteration and raise ValueError
        with pytest.raises(ValueError, match="Could not determine minimum interval"):
            _get_smallest_cron_interval_with_sampling("0 * * * *", "UTC")


def test_sampling_no_valid_interval_with_mock():
    """Test the ValueError when no valid interval can be determined.

    This test uses mocking to create a scenario where min_interval remains None,
    which should raise a ValueError.
    """
    from unittest.mock import patch

    with patch("dagster._utils.schedules.schedule_execution_time_iterator") as mock_iter:
        # Create a mock iterator that returns only negative or zero intervals
        base_time = datetime.datetime(2024, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        # All subsequent times go backward
        time1 = datetime.datetime(2024, 6, 1, 11, 0, 0, tzinfo=datetime.timezone.utc)
        time2 = datetime.datetime(2024, 6, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

        mock_iter.return_value = iter([base_time, time1, time2])

        # This should raise ValueError because no valid positive interval was found
        with pytest.raises(ValueError, match="Could not determine minimum interval"):
            _get_smallest_cron_interval_with_sampling("0 * * * *", "UTC")


def test_sampling_specific_day_patterns():
    """Test specific day patterns that require sampling due to variable month lengths.

    This tests the 1st and 15th pattern which has variable intervals
    depending on month length (can be 14-17 days).
    """
    # 1st and 15th of month - interval varies by month
    interval = _get_smallest_cron_interval_with_sampling("0 9 1,15 * *")
    # Minimum should be 14 days (e.g., Jan 15 -> Feb 1 in non-leap years can be 14-17 days)
    assert interval.days >= 14
    assert interval.days <= 17
