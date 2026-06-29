"""Unit tests for location and recency filters."""

from datetime import datetime, timedelta
import pytest

from job_agent.scrapers.base import JobPosting
from job_agent.filters.location import is_us_location, filter_us_only
from job_agent.filters.recency import filter_recent


def make_posting(location="New York, NY", hours_ago=1, url="https://example.com/job/1"):
    return JobPosting(
        title="Data Engineer",
        company="Test Corp",
        location=location,
        posted_date=datetime.utcnow() - timedelta(hours=hours_ago),
        apply_url=url,
        source="Test Source",
    )


class TestLocationFilter:

    def test_us_state_abbreviation(self):
        assert is_us_location(make_posting("Austin, TX")) is True

    def test_full_us_name(self):
        assert is_us_location(make_posting("United States")) is True

    def test_remote(self):
        assert is_us_location(make_posting("Remote")) is True

    def test_india_rejected(self):
        assert is_us_location(make_posting("Bangalore, India")) is False

    def test_india_city_rejected(self):
        assert is_us_location(make_posting("Hyderabad")) is False

    def test_canada_rejected(self):
        assert is_us_location(make_posting("Toronto, Canada")) is False

    def test_empty_location_passes(self):
        assert is_us_location(make_posting("")) is True

    def test_filter_removes_non_us(self):
        postings = [
            make_posting("New York, NY", url="https://example.com/1"),
            make_posting("Bangalore, India", url="https://example.com/2"),
            make_posting("Chicago, IL", url="https://example.com/3"),
        ]
        result = filter_us_only(postings)
        assert len(result) == 2
        assert all("India" not in p.location for p in result)


class TestRecencyFilter:

    def test_recent_posting_included(self):
        p = make_posting(hours_ago=2)
        assert filter_recent([p], hours=24) == [p]

    def test_old_posting_excluded(self):
        p = make_posting(hours_ago=26)
        assert filter_recent([p], hours=24) == []

    def test_no_date_included(self):
        p = JobPosting(
            title="Engineer", company="X", location="NY",
            posted_date=None, apply_url="https://example.com/x", source="X"
        )
        assert filter_recent([p], hours=24) == [p]

    def test_custom_window(self):
        p12 = make_posting(hours_ago=12, url="https://example.com/a")
        p36 = make_posting(hours_ago=36, url="https://example.com/b")
        assert filter_recent([p12, p36], hours=24) == [p12]
        assert filter_recent([p12, p36], hours=48) == [p12, p36]
