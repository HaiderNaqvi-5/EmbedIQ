import pytest
from app.services.url_normalizer import normalize_url

def test_normalize_url_basic():
    """Test that scheme and hostname are lowercased, and paths are preserved."""
    assert normalize_url("HTTP://EXAMPLE.COM/Path") == "http://example.com/Path"
    assert normalize_url("Https://Www.Example.Com/") == "https://www.example.com/"

def test_normalize_url_strip_fragment():
    """Test that URI fragments are stripped."""
    assert normalize_url("http://example.com/path#fragment") == "http://example.com/path"
    assert normalize_url("http://example.com/#top") == "http://example.com/"

def test_normalize_url_resolve_relative():
    """Test resolving relative URLs against base_origin."""
    assert normalize_url("/about", base_origin="https://example.com") == "https://example.com/about"
    assert normalize_url("contact", base_origin="https://example.com/") == "https://example.com/contact"
    assert normalize_url("../contact", base_origin="https://example.com/some/path") == "https://example.com/some/contact"
    assert normalize_url("/absolute/path", base_origin="https://example.com") == "https://example.com/absolute/path"

def test_normalize_url_tracking_params_removed():
    """Test that tracking/analytics parameters are removed."""
    url = "http://example.com/?utm_source=google&utm_medium=cpc&utm_campaign=spring&fbclid=abc&gclid=def&ref=twitter&mc_eid=123&_ga=456"
    assert normalize_url(url) == "http://example.com/"

def test_normalize_url_functional_params_retained_and_sorted():
    """Test that non-tracking parameters are retained and sorted alphabetically."""
    # query string sorting
    url = "http://example.com/?b=2&a=1&utm_source=foo&c=3"
    assert normalize_url(url) == "http://example.com/?a=1&b=2&c=3"

    # with list parameters
    url = "http://example.com/?x=2&x=1&y=3"
    assert normalize_url(url) == "http://example.com/?x=1&x=2&y=3"

def test_normalize_url_blank_params_kept():
    """Test that blank parameters are kept."""
    url = "http://example.com/?a=&b=2"
    assert normalize_url(url) == "http://example.com/?a=&b=2"

def test_normalize_url_strips_whitespace():
    """Test that surrounding whitespace is stripped from the URL."""
    assert normalize_url("  http://example.com/  ") == "http://example.com/"

def test_normalize_url_invalid_url():
    """Test that ValueError is raised for completely invalid URLs that fail to parse."""
    with pytest.raises(ValueError, match="Cannot parse URL"):
        normalize_url("http://[::1")
