"""
M9 Acceptance Test Suite — AT-001 through AT-010 (PRD Section 12)
=================================================================
Covers all 10 acceptance tests required for production readiness.
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient


async def _register_and_get_token(client: AsyncClient) -> tuple[str, str]:
    """Helper: register a fresh user, return (token, user_id)."""
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPass123!"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.text}"
    data = res.json()
    return data["access_token"], data.get("user_id", "")


# ---------------------------------------------------------------------------
# AT-001: User Registration & Authentication
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestAT001_Authentication:
    """AT-001: User can register, login, and access protected resources."""

    async def test_register_creates_account(self, client: AsyncClient):
        email = f"at001_{uuid.uuid4().hex[:6]}@test.com"
        res = await client.post(
            "/api/auth/register",
            json={"email": email, "password": "SecurePass123!"},
        )
        assert res.status_code in (200, 201)
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    async def test_duplicate_email_rejected(self, client: AsyncClient):
        email = f"dup_{uuid.uuid4().hex[:6]}@test.com"
        await client.post("/api/auth/register", json={"email": email, "password": "Pass1234!"})
        res = await client.post("/api/auth/register", json={"email": email, "password": "Pass1234!"})
        assert res.status_code == 400

    async def test_login_valid_credentials(self, client: AsyncClient):
        email = f"login_{uuid.uuid4().hex[:6]}@test.com"
        await client.post("/api/auth/register", json={"email": email, "password": "MyPass123!"})
        res = await client.post("/api/auth/login", json={"email": email, "password": "MyPass123!"})
        assert res.status_code == 200
        assert "access_token" in res.json()

    async def test_login_wrong_password_returns_401(self, client: AsyncClient):
        email = f"bad_{uuid.uuid4().hex[:6]}@test.com"
        await client.post("/api/auth/register", json={"email": email, "password": "CorrectPass1!"})
        res = await client.post("/api/auth/login", json={"email": email, "password": "WrongPass!"})
        assert res.status_code == 401

    async def test_me_returns_profile(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert "email" in data
        assert "id" in data

    async def test_me_without_token_returns_401(self, client: AsyncClient):
        res = await client.get("/api/auth/me")
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# AT-002: Bot Creation & Management
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestAT002_BotManagement:
    """AT-002: User can create, list, retrieve, update branding, and delete bots."""

    async def test_create_bot_returns_202(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        res = await client.post(
            "/api/bots",
            json={"website_url": "https://example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 202
        body = res.json()
        assert "bot_id" in body
        assert "job_id" in body
        assert body["status"] == "PENDING"

    async def test_create_bot_invalid_url_rejected(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        res = await client.post(
            "/api/bots",
            json={"website_url": "not-a-url"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422

    async def test_list_bots_only_returns_own(self, client: AsyncClient):
        token1, _ = await _register_and_get_token(client)
        token2, _ = await _register_and_get_token(client)
        # User1 creates a bot
        await client.post(
            "/api/bots",
            json={"website_url": "https://user1.com"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        # User2 should see 0 bots
        res = await client.get("/api/bots", headers={"Authorization": f"Bearer {token2}"})
        assert res.status_code == 200
        assert res.json() == []

    async def test_get_bot_detail(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        create_res = await client.post(
            "/api/bots",
            json={"website_url": "https://detail-test.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        bot_id = create_res.json()["bot_id"]
        res = await client.get(f"/api/bots/{bot_id}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        body = res.json()
        assert body["id"] == bot_id
        assert "total_pages_indexed" in body
        assert "total_chunks" in body

    async def test_other_user_cannot_access_bot(self, client: AsyncClient):
        token1, _ = await _register_and_get_token(client)
        token2, _ = await _register_and_get_token(client)
        create_res = await client.post(
            "/api/bots",
            json={"website_url": "https://private.com"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        bot_id = create_res.json()["bot_id"]
        res = await client.get(f"/api/bots/{bot_id}", headers={"Authorization": f"Bearer {token2}"})
        assert res.status_code == 404

    async def test_delete_bot_removes_it(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        create_res = await client.post(
            "/api/bots",
            json={"website_url": "https://todelete.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        bot_id = create_res.json()["bot_id"]
        del_res = await client.delete(f"/api/bots/{bot_id}", headers={"Authorization": f"Bearer {token}"})
        assert del_res.status_code == 204
        get_res = await client.get(f"/api/bots/{bot_id}", headers={"Authorization": f"Bearer {token}"})
        assert get_res.status_code == 404

    async def test_get_crawl_status_queued_when_new(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        create_res = await client.post(
            "/api/bots",
            json={"website_url": "https://statustest.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        bot_id = create_res.json()["bot_id"]
        res = await client.get(
            f"/api/bots/{bot_id}/crawl/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["status"] in ("QUEUED", "RUNNING", "COMPLETED", "FAILED")

    async def test_get_knowledge_empty_when_not_crawled(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        create_res = await client.post(
            "/api/bots",
            json={"website_url": "https://knowledgetest.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        bot_id = create_res.json()["bot_id"]
        res = await client.get(
            f"/api/bots/{bot_id}/knowledge",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["chunk_count"] == 0
        assert body["markdown_content"] is None


# ---------------------------------------------------------------------------
# AT-003: Branding Management
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestAT003_Branding:
    """AT-003: Branding defaults created on bot creation; PATCH updates applied."""

    async def test_default_branding_exists_after_creation(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        create_res = await client.post(
            "/api/bots",
            json={"website_url": "https://brand-test.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        bot_id = create_res.json()["bot_id"]
        res = await client.get(
            f"/api/bots/{bot_id}/branding",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert "primary_color" in body
        assert body["primary_color"].startswith("#")

    async def test_patch_branding_updates_fields(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        create_res = await client.post(
            "/api/bots",
            json={"website_url": "https://patch-brand.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        bot_id = create_res.json()["bot_id"]
        res = await client.patch(
            f"/api/bots/{bot_id}/branding",
            json={"company_name": "Test Corp", "primary_color": "#FF0000"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["company_name"] == "Test Corp"
        assert body["primary_color"] == "#FF0000"

    async def test_patch_branding_invalid_color_rejected(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        create_res = await client.post(
            "/api/bots",
            json={"website_url": "https://invalid-color.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        bot_id = create_res.json()["bot_id"]
        res = await client.patch(
            f"/api/bots/{bot_id}/branding",
            json={"primary_color": "not-a-color"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# AT-004: SSRF Guard
# ---------------------------------------------------------------------------

class TestAT004_SSRFGuard:
    """AT-004: SSRF validation blocks private/reserved URLs."""

    def test_localhost_rejected(self):
        from app.services.ssrf_guard import validate_url
        with pytest.raises(ValueError, match="blocked"):
            validate_url("http://127.0.0.1:8080/admin")

    def test_private_rfc1918_rejected(self):
        from app.services.ssrf_guard import validate_url
        with pytest.raises(ValueError, match="blocked"):
            validate_url("http://192.168.1.1/internal")

    def test_cloud_metadata_rejected(self):
        from app.services.ssrf_guard import validate_url
        with pytest.raises(ValueError):
            validate_url("http://169.254.169.254/latest/meta-data/")

    def test_internal_hostname_rejected(self):
        from app.services.ssrf_guard import validate_url
        with pytest.raises(ValueError, match="blocked"):
            validate_url("http://backend.internal/api")

    def test_embedded_credentials_rejected(self):
        from app.services.ssrf_guard import validate_url
        with pytest.raises(ValueError, match="credentials"):
            validate_url("http://user:pass@example.com/")

    def test_non_http_scheme_rejected(self):
        from app.services.ssrf_guard import validate_url
        with pytest.raises(ValueError, match="scheme"):
            validate_url("ftp://files.example.com/data")

    def test_valid_public_url_passes(self):
        from app.services.ssrf_guard import validate_url
        # Should not raise — example.com is publicly routable
        result = validate_url("https://httpbin.org/")
        assert result.startswith("https://")


# ---------------------------------------------------------------------------
# AT-005: Chunker — Page Boundary Enforcement
# ---------------------------------------------------------------------------

class TestAT005_Chunker:
    """AT-005: Chunker never merges content across page boundaries."""

    def test_chunks_respect_page_boundaries(self):
        from app.services.chunker import MarkdownChunker

        doc = """---
schema_version: "2.0"
bot_id: "test-bot"
crawl_job_id: "test-job"
website_url: "https://example.com"
website_name: "Example"
crawled_at: "2026-01-01T00:00:00Z"
total_pages_indexed: 2
failed_pages: 0
---

# Knowledge Base: Example

## Page: Home
- Source URL: https://example.com/
- Title: Home
- Content Hash: abc123

### Welcome
This is the home page content with lots of words to fill up space.
More content here for the home page section.

---

## Page: About
- Source URL: https://example.com/about
- Title: About Us
- Content Hash: def456

### Our Mission
This is the about page with completely different content.

---
"""
        chunker = MarkdownChunker(target_tokens=50, max_tokens=100, overlap_tokens=20)
        chunks = chunker.chunk_document(doc)

        # Every chunk must contain content from only one page
        for chunk in chunks:
            # Should not mix Home and About content
            has_home = "home" in chunk.content.lower() or "welcome" in chunk.content.lower()
            has_about = "about" in chunk.content.lower() or "mission" in chunk.content.lower()
            # A chunk may contain one OR neither (metadata lines), but never both page-exclusive terms
            assert not (has_home and has_about), (
                f"Chunk mixes page content: {chunk.content[:100]}"
            )

    def test_chunk_index_sequential(self):
        from app.services.chunker import MarkdownChunker

        doc = """---
schema_version: "2.0"
bot_id: "x"
crawl_job_id: "y"
website_url: "https://example.com"
website_name: "Ex"
crawled_at: "2026-01-01T00:00:00Z"
total_pages_indexed: 1
failed_pages: 0
---

# Knowledge Base: Ex

## Page: Home
- Source URL: https://example.com/
- Title: Home
- Content Hash: aaa

Some content here.

---
"""
        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(doc)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks))), f"Non-sequential indices: {indices}"

    def test_token_count_within_max(self):
        from app.services.chunker import MarkdownChunker

        long_paragraph = " ".join(["word"] * 2000)
        doc = f"""---
schema_version: "2.0"
bot_id: "x"
crawl_job_id: "y"
website_url: "https://example.com"
website_name: "Ex"
crawled_at: "2026-01-01T00:00:00Z"
total_pages_indexed: 1
failed_pages: 0
---

# Knowledge Base: Ex

## Page: Long
- Source URL: https://example.com/long
- Title: Long Page
- Content Hash: bbb

{long_paragraph}

---
"""
        chunker = MarkdownChunker(target_tokens=600, max_tokens=1000, overlap_tokens=100)
        chunks = chunker.chunk_document(doc)
        # All chunks must respect max_tokens (with some tolerance for approximation)
        for chunk in chunks:
            assert chunk.token_count <= 1100, (
                f"Chunk exceeds max tokens: {chunk.token_count} > 1100"
            )


# ---------------------------------------------------------------------------
# AT-006: URL Normalizer
# ---------------------------------------------------------------------------

class TestAT006_URLNormalizer:
    """AT-006: URL normalizer strips tracking params and handles origins correctly."""

    def test_strips_utm_params(self):
        from app.services.url_normalizer import normalize_url
        result = normalize_url("https://example.com/page?utm_source=google&utm_medium=cpc&content=main")
        assert "utm_source" not in result
        assert "utm_medium" not in result
        assert "content=main" in result

    def test_strips_fragment(self):
        from app.services.url_normalizer import normalize_url
        result = normalize_url("https://example.com/page#section")
        assert "#" not in result
        assert "section" not in result

    def test_extract_origin(self):
        from app.services.url_normalizer import extract_origin
        assert extract_origin("https://www.example.com/path?q=1") == "https://www.example.com"

    def test_same_origin_www_variant(self):
        from app.services.url_normalizer import is_same_origin
        assert is_same_origin("https://www.example.com/about", "https://example.com")

    def test_asset_url_detected(self):
        from app.services.url_normalizer import is_asset_url
        assert is_asset_url("https://example.com/image.jpg")
        assert is_asset_url("https://example.com/style.css")
        assert not is_asset_url("https://example.com/about")


# ---------------------------------------------------------------------------
# AT-007: Widget Config Endpoint (Public)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestAT007_WidgetConfig:
    """AT-007: Public widget config endpoint returns correct branding data."""

    async def test_widget_config_no_auth_required(self, client: AsyncClient):
        """Widget config endpoint must work without a JWT token."""
        token, _ = await _register_and_get_token(client)
        create_res = await client.post(
            "/api/bots",
            json={"website_url": "https://widget-test.com", "name": "Widget Bot"},
            headers={"Authorization": f"Bearer {token}"},
        )
        bot_id = create_res.json()["bot_id"]

        # No auth header
        res = await client.get(f"/api/widget/config/{bot_id}")
        assert res.status_code == 200
        body = res.json()
        assert "theme" in body
        assert "primary_color" in body["theme"]

    async def test_widget_config_unknown_bot_returns_404(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        res = await client.get(f"/api/widget/config/{fake_id}")
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# AT-008: Health Check
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestAT008_HealthCheck:
    """AT-008: Health endpoint returns proper status."""

    async def test_health_endpoint_returns_200(self, client: AsyncClient):
        res = await client.get("/api/health")
        assert res.status_code == 200
        body = res.json()
        assert "status" in body
        assert "services" in body

    async def test_root_endpoint_returns_200(self, client: AsyncClient):
        res = await client.get("/")
        assert res.status_code == 200
        body = res.json()
        assert body["name"] == "EmbedIQ"


# ---------------------------------------------------------------------------
# AT-009: Chat Endpoint Rejects Unready Bot
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestAT009_ChatGuard:
    """AT-009: Chat endpoint returns 409 when bot is not in READY state."""

    async def test_chat_rejects_pending_bot(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        create_res = await client.post(
            "/api/bots",
            json={"website_url": "https://not-ready.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        bot_id = create_res.json()["bot_id"]

        res = await client.post(
            "/api/chat",
            json={
                "bot_id": bot_id,
                "session_id": "sess_test",
                "message": "Hello?",
            },
        )
        # Bot is PENDING, must return 409
        assert res.status_code == 409

    async def test_chat_unknown_bot_returns_404(self, client: AsyncClient):
        res = await client.post(
            "/api/chat",
            json={
                "bot_id": str(uuid.uuid4()),
                "session_id": "sess_test",
                "message": "Hello?",
            },
        )
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# AT-010: Bot Name Defaults to Domain
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestAT010_BotNameDefault:
    """AT-010: When no name given, bot name defaults to the domain."""

    async def test_bot_name_defaults_to_domain(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        res = await client.post(
            "/api/bots",
            json={"website_url": "https://www.mycompany.com/products"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 202
        body = res.json()
        # Name should be "mycompany.com" (www stripped)
        assert body["name"] == "mycompany.com"

    async def test_explicit_name_preserved(self, client: AsyncClient):
        token, _ = await _register_and_get_token(client)
        res = await client.post(
            "/api/bots",
            json={"website_url": "https://example.com", "name": "My Custom Bot"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 202
        assert res.json()["name"] == "My Custom Bot"
