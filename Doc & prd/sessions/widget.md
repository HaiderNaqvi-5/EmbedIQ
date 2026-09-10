# Session: Widget.js & External Embed (Milestone 8)

## Status: COMPLETE

## Date
2026-09-09

## Summary
Implemented the standalone widget.js loader (<15KB) and the isolated iframe chat UI for embedding on external websites.

## Files Created

### Frontend
- `frontend/public/widget.js` — Standalone vanilla JS widget loader (~9.7KB uncompressed)
- `frontend/app/widget/chat/page.tsx` — Isolated iframe chat UI
- `frontend/app/widget/layout.tsx` — Minimal widget page layout
- `frontend/app/widget/test/page.tsx` — Test host page for widget testing

## widget.js Architecture

### Initialization
1. Reads `data-bot-id` from `document.currentScript`
2. Reads optional `data-api-url` for custom API base (defaults to API URL)
3. Fetches `GET /api/widget/config/{bot_id}` for branding
4. Injects Shadow DOM launcher button into document body

### Shadow DOM Isolation
- Full style isolation using Shadow DOM root
- Floating button in configured position (bottom-right/bottom-left)
- Chat panel: 400px wide × 600px tall iframe
- Mobile: fullscreen overlay when viewport < 640px

### postMessage Protocol
- Host → Iframe: PARENT_RESIZE, THEME_UPDATE
- Iframe → Host: WIDGET_TOGGLE_OPEN, WIDGET_TOGGLE_CLOSE, WIDGET_UNREAD_COUNT

## Chat Widget (`app/widget/chat/page.tsx`)
- Receives `bot_id` from URL query params
- Fetches branding from `/api/widget/config/{bot_id}`
- SSE streaming chat via fetch + ReadableStream
- Session persistence: `sess_{random}` stored in sessionStorage
- Sources shown as clickable links below bot messages
- Initial greeting: "Hi! I'm {company_name}'s AI assistant."
- Auto-scroll to bottom on new messages

## Embed Snippet
```html
<script 
  src="http://localhost:8000/widget.js" 
  data-bot-id="{bot_id}"
  defer
></script>
```

## Size
- widget.js: 9,698 bytes uncompressed (< 15KB target ✓)
