'use client';

import { useParams } from 'next/navigation';
import { useState } from 'react';
import Link from 'next/link';
import {
  Copy,
  CheckCircle2,
  Code2,
  ExternalLink,
  ChevronLeft,
  Terminal,
  Globe2,
  MessageSquare,
} from 'lucide-react';

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const WIDGET_URL =
  process.env.NEXT_PUBLIC_WIDGET_URL || 'http://localhost:3000';

export default function EmbedPage() {
  const params = useParams();
  const botId = params.bot_id as string;
  const [copied, setCopied] = useState(false);

  const embedSnippet = `<!-- EmbedIQ Widget -->
<script
  src="${WIDGET_URL}/widget.js"
  data-bot-id="${botId}"
  data-api-url="${API_URL}"
  data-base-url="${WIDGET_URL}"
  defer
></script>`;

  const copy = async () => {
    await navigator.clipboard.writeText(embedSnippet);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-7">
      <div>
        <Link
          href={`/dashboard/bots/${botId}`}
          className="mb-4 inline-flex items-center gap-1.5 text-sm text-[#8C9299] transition hover:text-[#F0C76A]"
        >
          <ChevronLeft className="h-4 w-4" />
          Bot overview
        </Link>

        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
          Installation
        </p>

        <h1 className="mt-2 text-2xl font-bold text-[#F5F5F3]">
          Embed Your Chatbot
        </h1>

        <p className="mt-2 text-sm text-[#8C9299]">
          Add one script to your website to make your assistant available to visitors.
        </p>
      </div>

      <section className="overflow-hidden rounded-2xl border border-[#C8CBD0]/10 bg-[#111418]">
        <div className="flex items-start gap-3 border-b border-[#C8CBD0]/10 px-6 py-5">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
            <Code2 className="h-5 w-5 text-[#D6A84F]" />
          </div>

          <div>
            <h2 className="font-semibold text-[#F5F5F3]">
              Installation Snippet
            </h2>
            <p className="mt-1 text-sm leading-6 text-[#8C9299]">
              Paste this before the{' '}
              <code className="rounded bg-[#1A1D21] px-1.5 py-0.5 font-mono text-[#C8CBD0]">
                {'</body>'}
              </code>{' '}
              tag on your website.
            </p>
          </div>
        </div>

        <div className="p-6">
          <div className="relative overflow-hidden rounded-xl border border-[#C8CBD0]/10 bg-[#080A0D]">
            <div className="flex items-center justify-between border-b border-[#C8CBD0]/10 px-4 py-2.5">
              <div className="flex items-center gap-2 text-xs text-[#8C9299]">
                <Terminal className="h-3.5 w-3.5 text-[#D6A84F]" />
                HTML
              </div>

              <button
                onClick={copy}
                className="inline-flex items-center gap-1.5 rounded-lg border border-[#C8CBD0]/10 bg-[#1A1D21] px-2.5 py-1.5 text-xs font-medium text-[#C8CBD0] transition hover:border-[#D6A84F]/30 hover:text-[#F0C76A]"
              >
                {copied ? (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}

                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>

            <pre className="overflow-x-auto p-5 font-mono text-xs leading-6 text-[#C8CBD0]">
              <code>{embedSnippet}</code>
            </pre>
          </div>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-6">
          <div className="mb-5 flex items-center gap-3">
            <Globe2 className="h-5 w-5 text-[#D6A84F]" />
            <h2 className="font-semibold text-[#F5F5F3]">
              How it works
            </h2>
          </div>

          <div className="space-y-4">
            {[
              'Paste the EmbedIQ snippet into your website.',
              'The lightweight loader creates the floating launcher.',
              'Visitors open the assistant without leaving your website.',
              'Questions are answered using this bot’s isolated knowledge base.',
            ].map((text, index) => (
              <div key={text} className="flex gap-3">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-[#D6A84F]/25 bg-[#D6A84F]/10 text-xs font-bold text-[#D6A84F]">
                  {index + 1}
                </div>
                <p className="text-sm leading-6 text-[#9EA3AA]">
                  {text}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-[#D6A84F]/25 bg-[#D6A84F]/5 p-6">
          <div className="mb-5 flex h-10 w-10 items-center justify-center rounded-xl border border-[#D6A84F]/25 bg-[#D6A84F]/10">
            <MessageSquare className="h-5 w-5 text-[#D6A84F]" />
          </div>

          <h2 className="font-semibold text-[#F5F5F3]">
            Test Your Widget
          </h2>

          <p className="mt-2 text-sm leading-6 text-[#9EA3AA]">
            Open the isolated test page to verify branding, chat behavior and
            retrieval before installing the widget on a live website.
          </p>

          <a
            href={`/widget/test?bot_id=${botId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#D6A84F] px-4 py-2.5 text-sm font-semibold text-[#080A0D] transition hover:bg-[#F0C76A]"
          >
            <ExternalLink className="h-4 w-4" />
            Open Test Page
          </a>
        </section>
      </div>

      <section className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] px-5 py-4">
        <div className="grid gap-4 text-xs sm:grid-cols-3">
          <div>
            <p className="text-[#5F656D]">Bot ID</p>
            <p className="mt-1 break-all font-mono text-[#9EA3AA]">
              {botId}
            </p>
          </div>

          <div>
            <p className="text-[#5F656D]">Widget script</p>
            <p className="mt-1 break-all font-mono text-[#9EA3AA]">
              {WIDGET_URL}/widget.js
            </p>
          </div>

          <div>
            <p className="text-[#5F656D]">Config API</p>
            <p className="mt-1 break-all font-mono text-[#9EA3AA]">
              {API_URL}/api/widget/config/{botId}
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
