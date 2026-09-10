'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  Plus,
  Bot,
  Globe,
  Loader2,
  AlertCircle,
  Clock,
  CheckCircle2,
  XCircle,
  Activity,
  Search,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';

interface BotSummary {
  id: string;
  name: string | null;
  website_url: string;
  status: string;
  created_at: string;
}

const STATUS_STYLES: Record<string, { label: string; className: string }> = {
  READY: {
    label: 'Ready',
    className:
      'border-emerald-500/20 bg-emerald-500/10 text-emerald-300',
  },
  READY_WITH_WARNINGS: {
    label: 'Ready with warnings',
    className:
      'border-amber-500/20 bg-amber-500/10 text-amber-300',
  },
  CRAWLING: {
    label: 'Crawling',
    className:
      'border-[#D6A84F]/25 bg-[#D6A84F]/10 text-[#F0C76A]',
  },
  PROCESSING: {
    label: 'Processing',
    className:
      'border-[#D6A84F]/25 bg-[#D6A84F]/10 text-[#F0C76A]',
  },
  INDEXING: {
    label: 'Indexing',
    className:
      'border-[#D6A84F]/25 bg-[#D6A84F]/10 text-[#F0C76A]',
  },
  PENDING: {
    label: 'Pending',
    className:
      'border-[#C8CBD0]/10 bg-[#C8CBD0]/5 text-[#C8CBD0]',
  },
  QUEUED: {
    label: 'Queued',
    className:
      'border-[#C8CBD0]/10 bg-[#C8CBD0]/5 text-[#C8CBD0]',
  },
  FAILED: {
    label: 'Failed',
    className:
      'border-red-500/20 bg-red-500/10 text-red-300',
  },
};

function StatusBadge({ status }: { status: string }) {
  const item =
    STATUS_STYLES[status] ?? {
      label: status,
      className:
        'border-[#C8CBD0]/10 bg-[#C8CBD0]/5 text-[#C8CBD0]',
    };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${item.className}`}
    >
      {item.label}
    </span>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function BotsPage() {
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
            : 'Failed to load bots.'
        )
      )
      .finally(() => setLoading(false));
  }, []);

  const filteredBots = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return bots;

    return bots.filter((bot) => {
      return (
        (bot.name || '').toLowerCase().includes(value) ||
        bot.website_url.toLowerCase().includes(value) ||
        bot.status.toLowerCase().includes(value)
      );
    });
  }, [bots, search]);

  const readyCount = bots.filter((bot) =>
    ['READY', 'READY_WITH_WARNINGS'].includes(bot.status)
  ).length;

  const processingCount = bots.filter((bot) =>
    [
      'PENDING',
      'QUEUED',
      'CRAWLING',
      'PROCESSING',
      'INDEXING',
    ].includes(bot.status)
  ).length;

  const failedCount = bots.filter(
    (bot) => bot.status === 'FAILED'
  ).length;

  return (
    <div className="space-y-8">
      <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
        <div>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
            Chatbots
          </p>

          <h1 className="text-3xl font-bold tracking-tight text-[#F5F5F3]">
            My Chatbots
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-[#8C9299]">
            Each bot belongs to one website and uses its own isolated
            knowledge base.
          </p>
        </div>

        <Link
          href="/dashboard/bots/new"
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#D6A84F] px-4 py-2.5 text-sm font-semibold text-[#080A0D] transition hover:bg-[#F0C76A]"
        >
          <Plus className="h-4 w-4" />
          Create New Bot
        </Link>
      </div>

      {!loading && bots.length > 0 && (
        <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
          {[
            {
              label: 'Total Bots',
              value: bots.length,
              icon: Bot,
            },
            {
              label: 'Ready',
              value: readyCount,
              icon: CheckCircle2,
            },
            {
              label: 'Processing',
              value: processingCount,
              icon: Activity,
            },
            {
              label: 'Failed',
              value: failedCount,
              icon: XCircle,
            },
          ].map(({ label, value, icon: Icon }) => (
            <div
              key={label}
              className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-4"
            >
              <Icon className="mb-3 h-4 w-4 text-[#D6A84F]" />
              <p className="text-2xl font-bold text-[#F5F5F3]">
                {value}
              </p>
              <p className="mt-1 text-xs text-[#8C9299]">
                {label}
              </p>
            </div>
          ))}
        </div>
      )}

      {!loading && bots.length > 0 && (
        <div className="relative max-w-md">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#5F656D]" />

          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search bots by name, website or status..."
            className="w-full rounded-xl border border-[#C8CBD0]/10 bg-[#111418] py-2.5 pl-10 pr-4 text-sm text-[#F5F5F3] outline-none transition placeholder:text-[#5F656D] focus:border-[#D6A84F]/40 focus:ring-2 focus:ring-[#D6A84F]/10"
          />
        </div>
      )}

      {loading && (
        <div className="flex min-h-[320px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-[#D6A84F]" />
        </div>
      )}

      {!loading && error && (
        <div className="flex items-start gap-3 rounded-2xl border border-red-500/20 bg-red-500/5 px-5 py-4 text-sm text-red-300">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && bots.length === 0 && (
        <section className="rounded-2xl border border-dashed border-[#C8CBD0]/15 bg-[#111418] px-6 py-20 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
            <Bot className="h-6 w-6 text-[#D6A84F]" />
          </div>

          <h2 className="mt-5 text-lg font-semibold text-[#F5F5F3]">
            No chatbots yet
          </h2>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[#8C9299]">
            Create your first chatbot by entering a website URL.
            EmbedIQ will crawl the website and build its isolated
            knowledge base.
          </p>

          <Link
            href="/dashboard/bots/new"
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#D6A84F] px-4 py-2.5 text-sm font-semibold text-[#080A0D] transition hover:bg-[#F0C76A]"
          >
            <Plus className="h-4 w-4" />
            Create Your First Bot
          </Link>
        </section>
      )}

      {!loading &&
        !error &&
        bots.length > 0 &&
        filteredBots.length === 0 && (
          <div className="rounded-2xl border border-dashed border-[#C8CBD0]/15 bg-[#111418] p-10 text-center">
            <Search className="mx-auto h-6 w-6 text-[#5F656D]" />
            <p className="mt-3 font-medium text-[#C8CBD0]">
              No matching bots
            </p>
            <p className="mt-1 text-sm text-[#8C9299]">
              Try a different search term.
            </p>
          </div>
        )}

      {!loading &&
        !error &&
        filteredBots.length > 0 && (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
            {filteredBots.map((bot) => (
              <Link
                key={bot.id}
                href={`/dashboard/bots/${bot.id}`}
                className="group flex min-h-[210px] flex-col rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5 transition hover:-translate-y-0.5 hover:border-[#D6A84F]/40 hover:bg-[#15181C]"
              >
                <div className="mb-5 flex items-start justify-between gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
                    <Bot className="h-5 w-5 text-[#D6A84F]" />
                  </div>

                  <StatusBadge status={bot.status} />
                </div>

                <h2 className="truncate text-base font-semibold text-[#F5F5F3] transition group-hover:text-[#F0C76A]">
                  {bot.name || 'Untitled Bot'}
                </h2>

                <div className="mt-2 flex min-w-0 items-center gap-2 text-sm text-[#8C9299]">
                  <Globe className="h-4 w-4 shrink-0" />
                  <span className="truncate">
                    {bot.website_url}
                  </span>
                </div>

                <div className="mt-auto flex items-center gap-2 border-t border-[#C8CBD0]/10 pt-4 text-xs text-[#5F656D]">
                  <Clock className="h-3.5 w-3.5" />
                  Created {formatDate(bot.created_at)}
                </div>
              </Link>
            ))}
          </div>
        )}
    </div>
  );
}
