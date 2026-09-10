# Session: Management Dashboard (Milestone 7)

## Status: COMPLETE

## Date
2026-09-09

## Summary
Implemented the full Next.js 14 App Router management dashboard with authentication, bot management UI, and all detail pages.

## Files Created

### Auth Pages
- `frontend/app/(auth)/layout.tsx` — Centered layout for auth pages
- `frontend/app/(auth)/login/page.tsx` — Login form (POST /api/auth/login)
- `frontend/app/(auth)/register/page.tsx` — Registration form (POST /api/auth/register)

### Dashboard Pages
- `frontend/app/(dashboard)/layout.tsx` — Sidebar layout with AuthGuard
- `frontend/app/(dashboard)/page.tsx` — Redirect to /bots
- `frontend/app/(dashboard)/bots/page.tsx` — Bot list grid with status badges
- `frontend/app/(dashboard)/bots/new/page.tsx` — Bot creation wizard
- `frontend/app/(dashboard)/bots/[bot_id]/page.tsx` — Bot detail overview
- `frontend/app/(dashboard)/bots/[bot_id]/crawl/page.tsx` — Real-time crawl progress
- `frontend/app/(dashboard)/bots/[bot_id]/knowledge/page.tsx` — Knowledge inspector
- `frontend/app/(dashboard)/bots/[bot_id]/branding/page.tsx` — Branding customization
- `frontend/app/(dashboard)/bots/[bot_id]/embed/page.tsx` — Embed snippet generator

### Utilities
- `frontend/lib/api.ts` — Typed API client with JWT Bearer auth
- `frontend/lib/auth.ts` — Token storage helpers

## Feature Details

### Auth System
- JWT token stored as `embediq_token` in localStorage
- AuthGuard in dashboard layout redirects unauthenticated users to /login

### Bot List (`/bots`)
- Color-coded status badges: READY=green, CRAWLING=blue, PENDING=yellow, FAILED=red
- Empty state message for new users

### Crawl Progress (`/bots/{id}/crawl`)
- Pipeline stage indicators (10 stages: VALIDATING → COMPLETED)
- Auto-polls GET /api/bots/{id}/crawl/status every 3 seconds while active
- Progress bar for page crawling progress

### Branding Editor (`/bots/{id}/branding`)
- Color pickers for primary, background, text colors
- Live preview panel with widget button preview
- Position (bottom-right/bottom-left) and theme (light/dark) selectors

### Embed Snippet (`/bots/{id}/embed`)
- Formatted code block with copy-to-clipboard
- Link to widget test page
- Bot ID and API URL reference

## Authentication Flow
1. User visits /login or /register
2. On success: token saved to localStorage, redirect to /bots
3. Subsequent requests: Authorization: Bearer {token} header
4. On 401: redirect to /login
