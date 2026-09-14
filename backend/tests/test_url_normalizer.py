import pytest
from app.services.url_normalizer import (
    normalize_url,
    extract_origin,
    is_same_origin,
    is_asset_url,
)

class TestNormalizeUrl:
    def test_basic_normalization(self):
        url = "HTTP://Example.com/Path/To/Page#fragment"
        assert normalize_url(url) == "http://example.com/Path/To/Page"

    def test_relative_url_with_base_origin(self):
        assert normalize_url("/about", base_origin="https://example.com") == "https://example.com/about"
        assert normalize_url("../contact", base_origin="https://example.com/subpath/") == "https://example.com/contact"

    def test_strips_fragments(self):
        assert normalize_url("https://example.com/page#section") == "https://example.com/page"
        assert normalize_url("https://example.com/page#") == "https://example.com/page"

    def test_cleans_tracking_query_params(self):
        url = "https://example.com/?utm_source=twitter&q=search&fbclid=123&utm_campaign=summer&valid=true"
        # query params should be sorted: q=search&valid=true
        assert normalize_url(url) == "https://example.com/?q=search&valid=true"

    def test_cleans_all_strip_patterns(self):
        url = "https://example.com/?utm_medium=email&fbclid=abc&gclid=def&ref=ghi&mc_eid=jkl&_ga=mno"
        # urlunparse with empty path and empty query still produces a trailing slash if there's no path but there is a slash originally?
        # actually urlparse of "https://example.com/" puts "/" in path.
        assert normalize_url(url) == "https://example.com/"

    def test_retains_functional_query_params(self):
        url = "https://example.com/?page=2&sort=desc"
        assert normalize_url(url) == "https://example.com/?page=2&sort=desc"

    def test_empty_query_params_are_retained(self):
        url = "https://example.com/?empty=&valid=yes"
        # order: empty=&valid=yes
        assert normalize_url(url) == "https://example.com/?empty=&valid=yes"

    def test_invalid_url(self):
        # urlparse doesn't raise exception for string URLs easily.
        # But if we pass an object that raises when string methods are called or when urlparse fails.
        # Integer will raise an AttributeError in url.strip() inside normalize_url.
        with pytest.raises(Exception):
            normalize_url(123)

class TestExtractOrigin:
    def test_extract_basic_origin(self):
        assert extract_origin("HTTPS://EXAMPLE.COM/path/to/page?q=1#frag") == "https://example.com"

    def test_extract_with_port(self):
        assert extract_origin("http://example.com:8080/path") == "http://example.com:8080"

    def test_missing_scheme_or_host(self):
        with pytest.raises(ValueError, match="is missing scheme or host"):
            extract_origin("example.com/path")
        with pytest.raises(ValueError, match="is missing scheme or host"):
            extract_origin("http:///path")

    def test_invalid_url_for_origin(self):
        with pytest.raises(Exception):
            extract_origin(123)

class TestIsSameOrigin:
    def test_same_origin(self):
        assert is_same_origin("https://example.com/page1", "https://example.com")

    def test_www_equivalence(self):
        assert is_same_origin("https://www.example.com/page", "https://example.com")
        assert is_same_origin("https://example.com/page", "https://www.example.com")
        assert is_same_origin("https://www.example.com/page", "https://www.example.com")

    def test_different_subdomain(self):
        assert not is_same_origin("https://blog.example.com/page", "https://example.com")
        assert not is_same_origin("https://example.com/page", "https://blog.example.com")

    def test_completely_different_origin(self):
        assert not is_same_origin("https://google.com", "https://example.com")

    def test_invalid_urls(self):
        # urlparse handles invalid ports without error but returns strange results sometimes.
        # passing int will cause exception, which is caught and returns False in is_same_origin
        assert not is_same_origin(123, "https://example.com")

class TestIsAssetUrl:
    @pytest.mark.parametrize("extension", [
        ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".mp4", ".zip",
        ".css", ".js", ".woff", ".woff2", ".ttf", ".eot", ".ico", ".webp",
        ".avif", ".mp3", ".wav", ".avi", ".mov"
    ])
    def test_known_asset_extensions(self, extension):
        assert is_asset_url(f"https://example.com/file{extension}")
        assert is_asset_url(f"https://example.com/path/to/file{extension.upper()}")

    def test_non_asset_extensions(self):
        assert not is_asset_url("https://example.com/file.html")
        assert not is_asset_url("https://example.com/file.txt")
        assert not is_asset_url("https://example.com/file")
        assert not is_asset_url("https://example.com/file/")
        # .xml is handled separately so it's technically in the list of assets in the code?
        # Let's check the code: _ASSET_EXTENSIONS includes ".xml"
        assert is_asset_url("https://example.com/sitemap.xml")

    def test_query_parameters_do_not_affect_asset_check(self):
        # wait urlparse will put query parameters in the query attribute, not in path.
        # actually let's just make sure it handles well.
        assert is_asset_url("https://example.com/image.png?width=200")
        assert not is_asset_url("https://example.com/page.html?ref=image.png")

    def test_invalid_url_for_asset(self):
        # Exception caught returns False
        assert not is_asset_url(123)
