import datetime

from dagster._utils.schedules import _get_smallest_cron_interval_with_sampling


def test_sampling_skips_negative_intervals_during_dst_fall_back():
    """Test that sampling correctly skips negative intervals during DST fall-back transitions.

    During DST fall-back transitions (e.g., when clocks "fall back" from 2 AM to 1 AM),
    consecutive cron ticks can have negative intervals when comparing timestamps.
    The sampling logic should skip these negative intervals and continue sampling
    to find the true minimum positive interval.

    This test verifies that the logic at schedules.py:1093-1097 correctly handles
    this scenario by skipping negative intervals that occur during DST transitions.
    """
    # Test with a timezone that has DST transitions (America/New_York)
    # For a daily schedule at 2 AM, we expect:
    # - Most days: 24-hour intervals
    # - Spring forward (DST start): 23-hour interval (2 AM -> next day 2 AM, but clocks jump)
    # - Fall back (DST end): When clocks fall back, we get a negative interval that should be skipped
    interval = _get_smallest_cron_interval_with_sampling("0 2 * * *", "America/New_York")

    # The minimum interval should be 23 hours (spring forward DST transition)
    # NOT negative (fall back DST transition should be skipped)
    assert interval == datetime.timedelta(hours=23)
    assert interval > datetime.timedelta(seconds=0), "Interval should be positive"


def test_sampling_skips_zero_intervals_during_dst_ambiguous_times():
    """Test that sampling correctly skips zero intervals during DST ambiguous times.

    During DST fall-back transitions, the same wall clock time can occur twice
    (differentiated by the 'fold' attribute). This can result in zero-interval
    gaps between consecutive ticks that represent the same local time but different
    actual moments in time.

    The sampling logic at schedules.py:1075-1089 should detect and skip these
    zero intervals when they represent DST ambiguous times (same hour/minute/second
    but different fold values).
    """
    # Hourly schedule at minute 30 in a DST timezone
    # During fall-back, 1:30 AM occurs twice (fold=0 and fold=1)
    # The sampling should skip the zero interval between these two occurrences
    interval = _get_smallest_cron_interval_with_sampling("30 * * * *", "America/New_York")

    # Should be 1 hour, not 0 (zero intervals during DST ambiguous times should be skipped)
    assert interval == datetime.timedelta(hours=1)
    assert interval > datetime.timedelta(seconds=0), "Interval should be positive, not zero"


def test_sampling_handles_dst_transitions_in_europe_berlin():
    """Test DST transition handling in Europe/Berlin timezone.

    Europe/Berlin has different DST transition dates than America/New_York.
    This test ensures the DST handling logic is timezone-agnostic and works
    correctly for different DST schedules.
    """
    # Daily at 2 AM in Europe/Berlin
    interval = _get_smallest_cron_interval_with_sampling("0 2 * * *", "Europe/Berlin")

    # Should capture the 23-hour interval during spring forward
    # Negative intervals during fall back should be skipped
    assert interval == datetime.timedelta(hours=23)
    assert interval > datetime.timedelta(seconds=0)


def test_sampling_handles_dst_with_hourly_schedule():
    """Test that hourly schedules correctly handle DST transitions.

    Hourly schedules should maintain their 1-hour minimum interval even during
    DST transitions. The sampling should skip any negative or zero intervals
    that might occur during fall-back transitions.
    """
    # Hourly schedule in America/New_York
    interval = _get_smallest_cron_interval_with_sampling("0 * * * *", "America/New_York")

    # Should be exactly 1 hour - DST doesn't affect hourly schedules' minimum interval
    assert interval == datetime.timedelta(hours=1)


def test_sampling_handles_dst_with_multiple_daily_times():
    """Test DST handling with multiple execution times per day.

    When a schedule runs multiple times per day, DST transitions might create
    negative intervals between some ticks. The sampling should skip these and
    find the true minimum positive interval.
    """
    # Twice daily: midnight and noon in America/New_York
    interval = _get_smallest_cron_interval_with_sampling("0 0,12 * * *", "America/New_York")

    # Minimum interval should be 12 hours (between midnight and noon on same day)
    # Any negative intervals from DST should be skipped
    assert interval == datetime.timedelta(hours=12)
    assert interval > datetime.timedelta(seconds=0)


def test_sampling_handles_weekly_schedule_across_dst():
    """Test that weekly schedules correctly handle DST transitions.

    Weekly schedules should maintain their 7-day minimum interval.
    DST transitions might create slight variations (23 or 25 hour intervals
    on the transition day), but the sampling should find the correct minimum.
    """
    # Weekly on Monday at 2 AM in America/New_York
    interval = _get_smallest_cron_interval_with_sampling("0 2 * * 1", "America/New_York")

    # Should be 7 days - DST on a single day shouldn't affect the minimum
    assert interval == datetime.timedelta(days=7)


def test_sampling_extensive_dst_coverage():
    """Test that sampling covers enough time to capture DST transitions.

    The sampling starts from 1 year ago and samples up to 1000 ticks or 20 years
    (whichever comes first). This test verifies that for a daily schedule,
    this is sufficient to capture at least one DST transition.
    """
    # Daily at times that are affected by DST transitions
    # In America/New_York, DST spring forward happens at 2 AM (clock jumps to 3 AM)
    # Only schedules exactly at 2 AM experience the 23-hour interval because that's
    # the exact moment that doesn't exist during spring forward
    test_times_with_expected = [
        ("0 1 * * *", datetime.timedelta(hours=24)),  # 1 AM - not affected by DST transition
        ("0 2 * * *", datetime.timedelta(hours=23)),  # 2 AM - DST transition hour (spring forward)
        ("0 3 * * *", datetime.timedelta(hours=24)),  # 3 AM - after spring forward, not affected
        ("0 4 * * *", datetime.timedelta(hours=24)),  # 4 AM - not affected by DST transition
    ]

    for cron_pattern, expected_interval in test_times_with_expected:
        interval = _get_smallest_cron_interval_with_sampling(cron_pattern, "America/New_York")

        # Should capture the expected interval (23 hours for DST-affected times, 24 for others)
        assert interval == expected_interval, (
            f"Pattern {cron_pattern} should have interval {expected_interval}, got {interval}"
        )
        assert interval > datetime.timedelta(seconds=0)


def test_sampling_no_dst_in_utc():
    """Test that UTC timezone (which has no DST) always returns consistent intervals.

    UTC has no DST transitions, so a daily schedule should always be exactly 24 hours.
    This serves as a control test to verify that DST-specific logic doesn't affect
    non-DST timezones.
    """
    # Daily at 2 AM in UTC (no DST)
    interval = _get_smallest_cron_interval_with_sampling("0 2 * * *", "UTC")

    # Should be exactly 24 hours - no DST transitions to create 23-hour intervals
    assert interval == datetime.timedelta(hours=24)
