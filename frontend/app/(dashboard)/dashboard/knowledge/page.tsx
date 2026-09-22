'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  Database,
  ArrowRight,
  Bot,
  Globe,
  Loader2,
  Search,
  CheckCircle2,
  AlertCircle,
  Clock,
  X,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';

interface BotSummary {
  id: string;
  name: string | null;
  website_url: string;
  status: string;
  created_at: string;
}

function statusClasses(status: string) {
  if (status === 'READY') {
    return 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300';
  }

  if (status === 'READY_WITH_WARNINGS') {
    return 'border-amber-500/20 bg-amber-500/10 text-amber-300';
  }

  if (status === 'FAILED') {
    return 'border-red-500/20 bg-red-500/10 text-red-300';
  }

  return 'border-[#D6A84F]/20 bg-[#D6A84F]/10 text-[#F0C76A]';
}

export default function KnowledgePage() {
  const [bots, setBots] = useState<BotSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    apiRequest<BotSummary[]>('/api/bots')
      .then((data) => {
        setBots(data);
        setError(null);
      })
      .catch((err: unknown) =>
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load knowledge bases.'
        )
      )
      .finally(() => setLoading(false));
  }, []);

  const filteredBots = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return bots;

    return bots.filter(
      (bot) =>
        (bot.name || '').toLowerCase().includes(value) ||
        bot.website_url.toLowerCase().includes(value)
    );
  }, [bots, search]);

  const available = bots.filter((bot) =>
    ['READY', 'READY_WITH_WARNINGS'].includes(bot.status)
  ).length;

  return (
    <div className="space-y-8">
      <div>
        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
          Knowledge
        </p>

        <h1 className="text-3xl font-bold tracking-tight text-[#F5F5F3]">
          Knowledge Bases
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-[#9EA3AA]">
          Each chatbot owns a separate website knowledge base.
          Select a bot to inspect its indexed content.
        </p>
      </div>

      {!loading && !error && bots.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5">
            <Bot className="mb-4 h-4 w-4 text-[#D6A84F]" />
            <p className="text-2xl font-bold text-[#F5F5F3]">
              {bots.length}
            </p>
            <p className="mt-1 text-sm text-[#8C9299]">
              Total bots
            </p>
          </div>

          <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5">
            <Database className="mb-4 h-4 w-4 text-[#D6A84F]" />
            <p className="text-2xl font-bold text-[#F5F5F3]">
              {available}
            </p>
            <p className="mt-1 text-sm text-[#8C9299]">
              Available knowledge bases
            </p>
          </div>

          <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5">
            <Clock className="mb-4 h-4 w-4 text-[#D6A84F]" />
            <p className="text-2xl font-bold text-[#F5F5F3]">
              {bots.length - available}
            </p>
            <p className="mt-1 text-sm text-[#8C9299]">
              Processing or unavailable
            </p>
          </div>
        </div>
      )}

      {!loading && bots.length > 0 && (
        <div className="relative max-w-md">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#5F656D]" />

          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search knowledge bases..."
            aria-label="Search knowledge bases"
            className="w-full rounded-xl border border-[#C8CBD0]/10 bg-[#111418] py-2.5 pl-10 pr-10 text-sm text-[#F5F5F3] outline-none transition placeholder:text-[#5F656D] focus:border-[#D6A84F]/40 focus:ring-2 focus:ring-[#D6A84F]/10"
          />

          {search && (
            <button
              type="button"
              onClick={() => setSearch('')}
              aria-label="Clear search"
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-[#5F656D] transition hover:bg-[#1A1D21] hover:text-[#C8CBD0] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#D6A84F]/50"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      )}

      {loading && (
        <div className="flex min-h-[320px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-[#D6A84F]" />
        </div>
      )}

      {!loading && error && (
        <div className="flex gap-3 rounded-2xl border border-red-500/20 bg-red-500/5 p-5 text-sm text-red-300">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
          {error}
        </div>
      )}

      {!loading && !error && bots.length === 0 && (
        <section className="rounded-2xl border border-dashed border-[#C8CBD0]/15 bg-[#111418] px-6 py-16 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
            <Database className="h-5 w-5 text-[#D6A84F]" />
          </div>

          <h2 className="mt-4 font-semibold text-[#F5F5F3]">
            No knowledge bases yet
          </h2>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[#8C9299]">
            Create a chatbot and EmbedIQ will crawl its website,
            generate the canonical knowledge base and index it.
          </p>

          <Link
            href="/dashboard/bots/new"
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#D6A84F] px-4 py-2.5 text-sm font-semibold text-[#080A0D] transition hover:bg-[#F0C76A]"
          >
            Create Bot
            <ArrowRight className="h-4 w-4" />
          </Link>
        </section>
      )}

      {!loading &&
        !error &&
        filteredBots.length > 0 && (
          <div className="overflow-hidden rounded-2xl border border-[#C8CBD0]/10 bg-[#111418]">
            <div className="border-b border-[#C8CBD0]/10 px-6 py-5">
              <h2 className="font-semibold text-[#F5F5F3]">
                Bot Knowledge Bases
              </h2>
              <p className="mt-1 text-sm text-[#8C9299]">
                Open a bot to inspect its canonical website knowledge.
              </p>
            </div>

            <div>
              {filteredBots.map((bot, index) => {
                const ready = [
                  'READY',
                  'READY_WITH_WARNINGS',
                ].includes(bot.status);

                return (
                  <Link
                    key={bot.id}
                    href={
                      ready
                        ? `/dashboard/bots/${bot.id}/knowledge`
                        : `/dashboard/bots/${bot.id}`
                    }
                    className={`group flex items-center gap-4 px-6 py-5 transition hover:bg-[#1A1D21] ${
                      index !== filteredBots.length - 1
                        ? 'border-b border-[#C8CBD0]/10'
                        : ''
                    }`}
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
                      <Database className="h-5 w-5 text-[#D6A84F]" />
                    </div>

                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium text-[#F5F5F3] transition group-hover:text-[#F0C76A]">
                        {bot.name || 'Untitled Bot'}
                      </p>

                      <div className="mt-1 flex items-center gap-1.5 text-xs text-[#8C9299]">
                        <Globe className="h-3.5 w-3.5 shrink-0" />
                        <span className="truncate">
                          {bot.website_url}
                        </span>
                      </div>
                    </div>

                    <span
                      className={`hidden rounded-full border px-2.5 py-1 text-xs font-semibold sm:inline-flex ${statusClasses(
                        bot.status
                      )}`}
                    >
                      {bot.status.replaceAll('_', ' ')}
                    </span>

                    {ready ? (
                      <ArrowRight className="h-4 w-4 shrink-0 text-[#5F656D] transition group-hover:translate-x-1 group-hover:text-[#D6A84F]" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-[#5F656D]" />
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        )}

      {!loading &&
        !error &&
        bots.length > 0 &&
        filteredBots.length === 0 && (
          <div className="rounded-2xl border border-dashed border-[#C8CBD0]/15 bg-[#111418] p-10 text-center">
            <Search className="mx-auto h-6 w-6 text-[#5F656D]" />
            <p className="mt-3 font-medium text-[#C8CBD0]">
              No matching knowledge bases
            </p>
          </div>
        )}
    </div>
  );
}
