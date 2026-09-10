'use client';
/**
 * EmbedIQ Widget Chat Page — /widget/chat
 *
 * Hosted inside the widget.js iframe. Features:
 * - Fetches bot branding from GET /api/widget/config/{bot_id}
 * - Streams answers via POST /api/chat/stream (SSE over fetch)
 * - Persists session_id in sessionStorage
 * - Bidirectional postMessage with host (PARENT_RESIZE, THEME_UPDATE incoming;
 *   WIDGET_TOGGLE_CLOSE, WIDGET_UNREAD_COUNT outgoing)
 * - Mobile fullscreen via postMessage signal from host
 */
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Suspense, useEffect, useRef, useState, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
/* ─────────────────────────────────────────────────────────────────────────── */
/*  Types                                                                      */
/* ─────────────────────────────────────────────────────────────────────────── */
interface Source {
  url: string;
  title: string;
}
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  streaming?: boolean;
}
interface BrandTheme {
  primary_color: string;
  background_color: string;
  text_color: string;
  font_family: string;
  border_radius: string;
  position: string;
}
interface WidgetConfig {
  bot_id: string;
  company_name: string;
  logo_url?: string;
  theme: BrandTheme;
}
/* ─────────────────────────────────────────────────────────────────────────── */
/*  Helpers                                                                    */
/* ─────────────────────────────────────────────────────────────────────────── */
function uid(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}
function sanitizeSources(sources: Source[]): Source[] {
  const seen = new Set<string>();
  const result: Source[] = [];

  for (const source of sources) {
    if (!source || typeof source.url !== 'string') continue;

    const url = source.url.trim();
    if (!url || seen.has(url)) continue;

    try {
      const parsed = new URL(url);

      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        continue;
      }
    } catch {
      continue;
    }

    seen.add(url);

    result.push({
      url,
      title:
        typeof source.title === 'string' && source.title.trim()
          ? source.title.trim()
          : url,
    });

    // Narrow widgets become noisy with long source lists.
    if (result.length >= 4) break;
  }

  return result;
}

function getOrCreateSession(botId: string): string {
  const key = `embediq_session_${botId}`;
  let sid = sessionStorage.getItem(key);
  if (!sid) {
    sid = 'sess_' + uid();
    sessionStorage.setItem(key, sid);
  }
  return sid;
}
const DEFAULT_THEME: BrandTheme = {
  primary_color: '#2563EB',
  background_color: '#FFFFFF',
  text_color: '#111827',
  font_family: 'Inter, sans-serif',
  border_radius: '12px',
  position: 'bottom-right',
};
/* ─────────────────────────────────────────────────────────────────────────── */
/*  Typing indicator component                                                  */
/* ─────────────────────────────────────────────────────────────────────────── */
function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1 py-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="inline-block w-2 h-2 rounded-full bg-current opacity-60 animate-bounce"
          style={{ animationDelay: `${i * 0.15}s`, animationDuration: '0.9s' }}
        />
      ))}
    </span>
  );
}
/* ─────────────────────────────────────────────────────────────────────────── */
/*  Main page component                                                         */
/* ─────────────────────────────────────────────────────────────────────────── */
function WidgetChatContent() {
  const params   = useSearchParams();
  const botId       = params.get('bot_id') ?? '';
  const apiBase     = params.get('api_url') ?? 'http://localhost:8000';
  const parentOrigin = params.get('parent_origin') ?? '';
  const [config,    setConfig]    = useState<WidgetConfig | null>(null);
  const [theme,     setTheme]     = useState<BrandTheme>(DEFAULT_THEME);
  const [messages,  setMessages]  = useState<Message[]>([]);
  const [input,     setInput]     = useState('');
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState<string | null>(null);
  const [isMobile,  setIsMobile]  = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef       = useRef<HTMLInputElement>(null);
  const sessionId      = useRef<string>('');
  const abortRef       = useRef<AbortController | null>(null);
  /* ── Scroll helper ── */
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);
  useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);
  /* ── Fetch branding config ── */
  useEffect(() => {
    if (!botId) return;
    sessionId.current = getOrCreateSession(botId);
    fetch(`${apiBase}/api/widget/config/${botId}`)
      .then((r) => r.json())
      .then((data: WidgetConfig) => {
        setConfig(data);
        setTheme({ ...DEFAULT_THEME, ...(data.theme || {}) });
        // Add greeting
        const name = data.company_name || 'our';
        setMessages([
          {
            id: 'greeting',
            role: 'assistant',
            content: `Hi! I'm ${name}'s AI assistant. How can I help you today?`,
          },
        ]);
      })
      .catch(() => {
        setTheme(DEFAULT_THEME);
        setMessages([
          {
            id: 'greeting',
            role: 'assistant',
            content: "Hi! I'm your AI assistant. How can I help you today?",
          },
        ]);
      });
  }, [botId, apiBase]);
  /* ── Listen for postMessage from host ── */
  useEffect(() => {
    function handleMessage(e: MessageEvent) {
      // Only accept messages from the actual parent page that created
      // this iframe. Never trust unrelated windows or wildcard senders.
      if (e.source !== window.parent) return;
      if (!parentOrigin || e.origin !== parentOrigin) return;
      if (!e.data || typeof e.data !== 'object') return;

      if (e.data.type === 'PARENT_RESIZE') {
        setIsMobile(!!e.data.mobile);
      }
      if (e.data.type === 'THEME_UPDATE' && e.data.theme) {
        setTheme((prev) => ({ ...prev, ...e.data.theme }));
      }
    }
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [parentOrigin]);
  /* ── Notify host of unread count when messages arrive ── */
  useEffect(() => {
    const unread = messages.filter((m) => m.role === 'assistant' && m.id !== 'greeting').length;
    if (parentOrigin) {
      window.parent.postMessage(
        { type: 'WIDGET_UNREAD_COUNT', count: unread },
        parentOrigin
      );
    }
  }, [messages]);
  /* ── SSE streaming send ── */
  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || loading || !botId) return;
    setInput('');
    setError(null);
    const userMsg: Message = { id: uid(), role: 'user', content: text };
    const assistantId = uid();
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      streaming: true,
    };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setLoading(true);
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const response = await fetch(`${apiBase}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bot_id: botId,
          session_id: sessionId.current,
          message: text,
        }),
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const reader  = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer    = '';
      let fullText  = '';
      let sources: Source[] = [];
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';   // keep partial last line
        for (const line of lines) {
          if (line.startsWith('event: ')) continue; // event name line
          if (!line.startsWith('data: '))  continue;
          const raw = line.slice(6).trim();
          if (!raw || raw === '[DONE]') continue;
          let parsed: unknown;
          try {
            parsed = JSON.parse(raw);
          } catch {
            // Ignore malformed/non-JSON SSE payloads only.
            continue;
          }

          if (
            typeof parsed === 'object' &&
            parsed !== null &&
            'text' in parsed
          ) {
            const token = (parsed as { text?: unknown }).text;
            if (typeof token === 'string') {
              fullText += token;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: fullText, streaming: true }
                    : m
                )
              );
            }
          } else if (Array.isArray(parsed)) {
            // sources event — array of {url, title}
            sources = sanitizeSources(parsed as Source[]);
          } else if (
            typeof parsed === 'object' &&
            parsed !== null &&
            'status' in parsed &&
            (parsed as { status?: unknown }).status === 'complete'
          ) {
            // done event — finalise
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: fullText, streaming: false, sources }
                  : m
              )
            );
          } else if (
            typeof parsed === 'object' &&
            parsed !== null &&
            ('code' in parsed || 'message' in parsed)
          ) {
            const payload = parsed as { message?: unknown };
            throw new Error(
              typeof payload.message === 'string'
                ? payload.message
                : 'Stream error'
            );
          }
        }
      }
      // Finalise if stream ended without done event
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: fullText || '…', streaming: false, sources }
            : m
        )
      );
    } catch (err: unknown) {
      if ((err as Error).name === 'AbortError') return;
      console.error('[EmbedIQ chat] stream error:', err);
      setError('Sorry, something went wrong. Please try again.');
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: 'Sorry, I encountered an error. Please try again.',
                streaming: false,
              }
            : m
        )
      );
    } finally {
      setLoading(false);
    }
  }, [input, loading, botId, apiBase]);
  /* ── Enter key handler ── */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  /* ── Close button handler (signals host) ── */
  const handleClose = () => {
    if (parentOrigin) {
      window.parent.postMessage(
        { type: 'WIDGET_TOGGLE_CLOSE' },
        parentOrigin
      );
    }
  };
  /* ── Derive CSS vars from theme ── */
  const pc  = theme.primary_color  || '#2563EB';
  const bg  = theme.background_color || '#FFFFFF';
  const tc  = theme.text_color     || '#111827';
  const ff  = theme.font_family    || 'Inter, sans-serif';
  const br  = theme.border_radius  || '12px';
  const companyName = config?.company_name || 'EmbedIQ';
  const logoUrl     = config?.logo_url;
  /* ─── Render ─────────────────────────────────────────────────────────────*/
  return (
    <div
      className="flex flex-col w-full overflow-hidden"
      style={{
        height: '100dvh',
        background: bg,
        color: tc,
        fontFamily: ff,
      }}
    >
      {/* ── Header ── */}
      <header
        className="flex items-center justify-between px-4 py-3.5 shrink-0 border-b border-black/5"
        style={{
          background: `linear-gradient(135deg, ${pc}, ${pc}E6)`,
          color: '#fff'
        }}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          {logoUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={logoUrl}
              alt={companyName + ' logo'}
              className="h-9 w-auto max-w-[120px] object-contain shrink-0"
              onError={(e) => { console.error('EmbedIQ logo failed to load:', logoUrl); (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
            />
          )}
          <div className="min-w-0">
            <p className="font-semibold text-sm leading-tight truncate">{companyName}</p>
            <p className="text-xs opacity-75 leading-tight">AI Assistant</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] opacity-60 hidden sm:block">Powered by EmbedIQ</span>
          <button
            onClick={handleClose}
            className="w-7 h-7 flex items-center justify-center rounded-full hover:bg-white/20 transition-colors"
            aria-label="Close chat"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </header>
      {/* ── Message list ── */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3" aria-live="polite" aria-label="Chat messages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className="max-w-[88%] px-3.5 py-2.5 text-sm leading-relaxed break-words shadow-sm"
              style={{
                borderRadius: br,
                ...(msg.role === 'user'
                  ? {
                      background: pc,
                      color: '#fff'
                    }
                  : {
                      background: '#f8fafc',
                      color: tc,
                      border: '1px solid #e2e8f0'
                    }),
              }}
            >
              {msg.streaming && !msg.content ? (
                <TypingDots />
              ) : msg.role === 'assistant' ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    p: ({ children }) => (
                      <p className="mb-2 last:mb-0 leading-relaxed">
                        {children}
                      </p>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-semibold">
                        {children}
                      </strong>
                    ),
                    ul: ({ children }) => (
                      <ul className="list-disc pl-5 my-2 space-y-1">
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="list-decimal pl-5 my-2 space-y-1">
                        {children}
                      </ol>
                    ),
                    li: ({ children }) => (
                      <li className="leading-relaxed">
                        {children}
                      </li>
                    ),
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-3">
                        <table className="w-full border-collapse text-xs">
                          {children}
                        </table>
                      </div>
                    ),
                    th: ({ children }) => (
                      <th className="border border-slate-300 px-2 py-1 text-left font-semibold">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="border border-slate-300 px-2 py-1 align-top">
                        {children}
                      </td>
                    ),
                    code: ({ children }) => (
                      <code className="rounded bg-black/10 px-1 py-0.5 text-[0.9em]">
                        {children}
                      </code>
                    ),
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              ) : (
                msg.content
              )}
              {msg.streaming && msg.content && (
                <span className="inline-block w-0.5 h-4 bg-current ml-0.5 animate-pulse align-middle" />
              )}
            </div>
            {/* Sources */}
            {!msg.streaming && msg.sources && msg.sources.length > 0 && (
              <div className="mt-2 max-w-[88%] space-y-1.5">
                <p className="text-[10px] text-slate-400 font-semibold uppercase tracking-[0.08em] px-1">
                  Sources
                </p>
                {msg.sources.map((src, i) => (
                  <a
                    key={i}
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-xs px-2.5 py-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 transition-colors truncate shadow-sm"
                    style={{ color: pc }}
                    title={src.url}
                  >
                    {src.title || src.url}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
        {/* Error banner */}
        {error && (
          <div className="text-center text-xs text-red-500 py-1">{error}</div>
        )}
        <div ref={messagesEndRef} />
      </div>
      {/* ── Powered by footer strip (mobile hidden) ── */}
      {!isMobile && (
        <div className="text-center text-[10px] text-slate-400 py-1.5 shrink-0">
          Powered by{' '}
          <span className="font-semibold tracking-wide" style={{ color: pc }}>
            EmbedIQ
          </span>
        </div>
      )}
      {/* ── Input area ── */}
      <div
        className="shrink-0 px-3.5 pb-3.5 pt-2.5 border-t bg-white/90 backdrop-blur-sm"
        style={{ borderColor: '#e2e8f0' }}
      >
        <div
          className="flex items-center gap-2 rounded-2xl border px-3 py-2.5 bg-white shadow-sm transition-all focus-within:shadow-md"
          style={{ borderColor: '#dbe3ec' }}
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question…"
            disabled={loading}
            className="flex-1 text-sm bg-transparent outline-none placeholder:text-slate-400 disabled:opacity-50 min-w-0"
            style={{ color: tc }}
            aria-label="Chat input"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            aria-label="Send message"
            className="shrink-0 w-9 h-9 flex items-center justify-center rounded-xl transition-all hover:scale-[1.03] active:scale-[0.97] disabled:opacity-40 disabled:hover:scale-100"
            style={{ background: pc, color: '#fff' }}
          >
            {loading ? (
              <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function WidgetChatFallback() {
  return (
    <div className="flex h-screen w-full items-center justify-center">
      <span className="text-sm text-slate-500">Loading chat...</span>
    </div>
  );
}

export default function WidgetChatPage() {
  return (
    <Suspense fallback={<WidgetChatFallback />}>
      <WidgetChatContent />
    </Suspense>
  );
}

