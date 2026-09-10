"""Tests for the content extractor (app.services.extractor)."""

import pytest

from app.services.extractor import extract_branding, extract_page_content


# ---------------------------------------------------------------------------
# Sample HTML fixtures
# ---------------------------------------------------------------------------

HTML_NOISE_HEAVY = """\
<html>
<head>
    <title>My Site | Best Products</title>
    <meta name="description" content="Great stuff here">
    <script>var tracking = true;</script>
    <style>body { color: red; }</style>
    <noscript>Enable JavaScript</noscript>
</head>
<body>
    <nav><a href="/">Home</a><a href="/about">About</a></nav>
    <header><p>Header content</p></header>
    <main>
        <h1>Welcome to Our Site</h1>
        <p>This is the primary content that should be extracted.</p>
        <p>Another paragraph with useful information for the user.</p>
    </main>
    <footer><p>Copyright 2025</p></footer>
    <aside><p>Sidebar stuff</p></aside>
</body>
</html>
"""

HTML_MAIN_CONTAINER = """\
<html>
<head><title>Article Page</title></head>
<body>
    <nav>Navigation bar</nav>
    <main>
        <h2>Introduction</h2>
        <p>Intro paragraph text goes here.</p>
        <h2>Details</h2>
        <p>Detailed information follows.</p>
    </main>
    <footer>Footer content</footer>
</body>
</html>
"""

HTML_HEADING_ORDER = """\
<html>
<body>
    <main>
        <h1>Page Title</h1>
        <p>Some text</p>
        <h2>Section One</h2>
        <p>Section one content.</p>
        <h3>Subsection</h3>
        <p>Subsection content.</p>
        <h2>Section Two</h2>
        <p>Section two content.</p>
    </main>
</body>
</html>
"""

HTML_COOKIE_BANNER = """\
<html>
<head><title>Clean Page</title></head>
<body>
    <div class="cookie-banner" id="consent-popup">Accept cookies</div>
    <div class="gdpr-overlay">GDPR notice</div>
    <main>
        <p>Actual page content that matters.</p>
    </main>
</body>
</html>
"""

HTML_BRANDING_FULL = """\
<html>
<head>
    <meta property="og:site_name" content="Acme Inc">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <link rel="icon" href="/favicon-32x32.png">
    <style>
        :root { --primary: #FF5733; }
    </style>
</head>
<body></body>
</html>
"""

HTML_BRANDING_TITLE_FALLBACK = """\
<html>
<head>
    <title>WidgetCo | Build Better Widgets</title>
</head>
<body></body>
</html>
"""

HTML_BRANDING_NO_LOGO = """\
<html>
<head>
    <meta property="og:site_name" content="NoLogo Corp">
</head>
<body></body>
</html>
"""


# ---------------------------------------------------------------------------
# extract_page_content tests
# ---------------------------------------------------------------------------


class TestNoiseRemoval:
    def test_script_removed(self):
        result = extract_page_content(HTML_NOISE_HEAVY, "https://example.com")
        assert "var tracking" not in result.clean_text

    def test_style_removed(self):
        result = extract_page_content(HTML_NOISE_HEAVY, "https://example.com")
        assert "color: red" not in result.clean_text

    def test_nav_removed(self):
        result = extract_page_content(HTML_NOISE_HEAVY, "https://example.com")
        assert "Home" not in result.clean_text

    def test_footer_removed(self):
        result = extract_page_content(HTML_NOISE_HEAVY, "https://example.com")
        assert "Copyright 2025" not in result.clean_text

    def test_cookie_banner_removed(self):
        result = extract_page_content(HTML_COOKIE_BANNER, "https://example.com")
        assert "Accept cookies" not in result.clean_text
        assert "GDPR notice" not in result.clean_text
        assert "Actual page content" in result.clean_text


class TestPrimaryContainer:
    def test_main_tag_extracted(self):
        result = extract_page_content(HTML_MAIN_CONTAINER, "https://example.com")
        assert "Intro paragraph text" in result.clean_text
        assert "Detailed information" in result.clean_text

    def test_nav_not_in_content(self):
        result = extract_page_content(HTML_MAIN_CONTAINER, "https://example.com")
        assert "Navigation bar" not in result.clean_text


class TestHeadingExtraction:
    def test_headings_in_document_order(self):
        result = extract_page_content(HTML_HEADING_ORDER, "https://example.com")

        texts = [h["text"] for h in result.headings]
        assert texts == ["Page Title", "Section One", "Subsection", "Section Two"]

    def test_heading_levels_correct(self):
        result = extract_page_content(HTML_HEADING_ORDER, "https://example.com")
        levels = [h["level"] for h in result.headings]
        assert levels == ["h1", "h2", "h3", "h2"]

    def test_title_from_title_tag(self):
        result = extract_page_content(HTML_MAIN_CONTAINER, "https://example.com")
        assert result.title == "Article Page"

    def test_meta_description_extracted(self):
        result = extract_page_content(HTML_NOISE_HEAVY, "https://example.com")
        assert result.description == "Great stuff here"


# ---------------------------------------------------------------------------
# extract_branding tests
# ---------------------------------------------------------------------------


class TestBrandingCompanyName:
    def test_from_og_site_name(self):
        branding = extract_branding(HTML_BRANDING_FULL, "https://example.com")
        assert branding.company_name == "Acme Inc"
        assert branding.confidence["company_name"] == pytest.approx(0.95)

    def test_fallback_to_title(self):
        branding = extract_branding(HTML_BRANDING_TITLE_FALLBACK, "https://example.com")
        assert branding.company_name == "WidgetCo"
        assert branding.confidence["company_name"] == pytest.approx(0.70)


class TestBrandingLogo:
    def test_logo_from_apple_touch_icon(self):
        branding = extract_branding(HTML_BRANDING_FULL, "https://example.com")
        assert branding.logo_url is not None
        assert "apple-touch-icon.png" in branding.logo_url
        assert branding.confidence["logo_url"] == pytest.approx(0.85)

    def test_logo_none_when_absent(self):
        branding = extract_branding(HTML_BRANDING_NO_LOGO, "https://example.com")
        assert branding.confidence["logo_url"] == pytest.approx(0.0)


class TestBrandingColor:
    def test_primary_color_from_css_variable(self):
        branding = extract_branding(HTML_BRANDING_FULL, "https://example.com")
        assert branding.primary_color == "#FF5733"
        assert branding.confidence["primary_color"] == pytest.approx(0.85)


class TestBrandingConfidence:
    def test_all_fields_have_confidence(self):
        branding = extract_branding(HTML_BRANDING_FULL, "https://example.com")
        assert "company_name" in branding.confidence
        assert "logo_url" in branding.confidence
        assert "favicon_url" in branding.confidence
        assert "primary_color" in branding.confidence

    def test_confidence_values_in_range(self):
        branding = extract_branding(HTML_BRANDING_FULL, "https://example.com")
        for key, val in branding.confidence.items():
            assert 0.0 <= val <= 1.0, f"confidence[{key}] = {val} out of range"
