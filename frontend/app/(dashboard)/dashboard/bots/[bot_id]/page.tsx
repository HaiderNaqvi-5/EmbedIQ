'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { apiRequest } from '@/lib/api';
import {
  Globe,
  Settings,
  Code,
  BarChart3,
  ChevronRight,
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  RefreshCw,
  Database,
  ExternalLink,
  Layers3,
} from 'lucide-react';

interface BotDetail {
  id: string;
  name: string;
  website_url: string;
  normalized_origin: string;
  status: string;
  last_error: string | null;
  created_at: string;
  updated_at: string;
  total_pages_indexed: number;
  total_chunks: number;
  branding: {
    company_name: string | null;
    primary_color: string;
  } | null;
}

const STATUS_CONFIG: Record<
  string,
  {
    label: string;
    classes: string;
    icon: React.ReactNode;
  }
> = {
  READY: {
    label: 'Ready',
    classes: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-300',
    icon: <CheckCircle className="h-4 w-4" />,
  },
  READY_WITH_WARNINGS: {
    label: 'Ready with warnings',
    classes: 'border-amber-500/25 bg-amber-500/10 text-amber-300',
    icon: <AlertCircle className="h-4 w-4" />,
  },
  CRAWLING: {
    label: 'Crawling',
    classes: 'border-[#D6A84F]/30 bg-[#D6A84F]/10 text-[#F0C76A]',
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
  },
  PENDING: {
    label: 'Pending',
    classes: 'border-[#C8CBD0]/15 bg-[#C8CBD0]/5 text-[#C8CBD0]',
    icon: <Clock className="h-4 w-4" />,
  },
  QUEUED: {
    label: 'Queued',
    classes: 'border-[#C8CBD0]/15 bg-[#C8CBD0]/5 text-[#C8CBD0]',
    icon: <Clock className="h-4 w-4" />,
  },
  PROCESSING: {
    label: 'Processing',
    classes: 'border-[#D6A84F]/30 bg-[#D6A84F]/10 text-[#F0C76A]',
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
  },
  INDEXING: {
    label: 'Indexing',
    classes: 'border-[#D6A84F]/30 bg-[#D6A84F]/10 text-[#F0C76A]',
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
  },
  FAILED: {
    label: 'Failed',
    classes: 'border-red-500/25 bg-red-500/10 text-red-300',
    icon: <XCircle className="h-4 w-4" />,
  },
};

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] ?? {
    label: status,
    classes: 'border-[#C8CBD0]/15 bg-[#C8CBD0]/5 text-[#C8CBD0]',
    icon: null,
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold ${config.classes}`}
    >
      {config.icon}
      {config.label}
    </span>
  );
}

const NAV_ITEMS = [
  {
    label: 'Crawl Progress',
    description: 'Monitor website discovery and processing.',
    href: 'crawl',
    icon: BarChart3,
  },
  {
    label: 'Knowledge Base',
    description: 'Inspect the indexed website knowledge.',
    href: 'knowledge',
    icon: Database,
  },
  {
    label: 'Branding',
    description: 'Customize your customer-facing assistant.',
    href: 'branding',
    icon: Settings,
  },
  {
    label: 'Embed Widget',
    description: 'Install the chatbot on your website.',
    href: 'embed',
    icon: Code,
  },
];

export default function BotDetailPage() {
  const params = useParams();
  const botId = params.bot_id as string;

  const [bot, setBot] = useState<BotDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBot = useCallback(
    async (silent = false) => {
      try {
        if (silent) setRefreshing(true);

        const data = await apiRequest<BotDetail>(
          `/api/bots/${botId}`
        );

        setBot(data);
        setError(null);
      } catch (err: unknown) {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load chatbot.'
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [botId]
  );

  useEffect(() => {
    fetchBot();
  }, [fetchBot]);

  useEffect(() => {
    if (
      !bot ||
      !['PENDING', 'QUEUED', 'CRAWLING', 'PROCESSING', 'INDEXING'].includes(
        bot.status
      )
    ) {
      return;
    }

    const interval = window.setInterval(() => {
      fetchBot(true);
    }, 5000);

    return () => window.clearInterval(interval);
  }, [bot?.status, fetchBot]);

  if (loading) {
    return (
      <div className="flex min-h-[420px] items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-[#D6A84F]" />
          <p className="mt-3 text-sm text-[#8C9299]">
            Loading chatbot...
          </p>
        </div>
      </div>
    );
  }

  if (error && !bot) {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
          <div>
            <h2 className="font-semibold text-red-300">
              Unable to load chatbot
            </h2>
            <p className="mt-1 text-sm text-red-300/70">
              {error}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!bot) return null;

  const displayName =
    bot.name ||
    bot.branding?.company_name ||
    'Untitled Bot';

  return (
    <div className="space-y-7">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-[#8C9299]">
        <Link
          href="/dashboard/bots"
          className="transition hover:text-[#F0C76A]"
        >
          My Bots
        </Link>

        <ChevronRight className="h-4 w-4" />

        <span className="truncate font-medium text-[#C8CBD0]">
          {displayName}
        </span>
      </div>

      {/* Main header */}
      <section className="overflow-hidden rounded-2xl border border-[#C8CBD0]/10 bg-[#111418]">
        <div className="border-b border-[#C8CBD0]/10 px-6 py-6 sm:px-7">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
            <div className="min-w-0">
              <div className="mb-3 flex flex-wrap items-center gap-3">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
                  Chatbot
                </p>

                <StatusBadge status={bot.status} />
              </div>

              <h1 className="truncate text-3xl font-bold tracking-tight text-[#F5F5F3]">
                {displayName}
              </h1>

              <a
                href={bot.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-3 inline-flex max-w-full items-center gap-2 text-sm text-[#9EA3AA] transition hover:text-[#F0C76A]"
              >
                <Globe className="h-4 w-4 shrink-0" />
                <span className="truncate">
                  {bot.website_url}
                </span>
                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
              </a>
            </div>

            <button
              onClick={() => fetchBot(true)}
              disabled={refreshing}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-[#C8CBD0]/15 bg-[#1A1D21] px-4 text-sm font-medium text-[#C8CBD0] transition hover:border-[#D6A84F]/40 hover:text-[#F0C76A] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RefreshCw
                className={`h-4 w-4 ${
                  refreshing ? 'animate-spin' : ''
                }`}
              />
              Refresh
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid divide-y divide-[#C8CBD0]/10 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
          <div className="px-6 py-5">
            <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg border border-[#D6A84F]/20 bg-[#D6A84F]/10">
              <Globe className="h-4 w-4 text-[#D6A84F]" />
            </div>
            <p className="text-2xl font-bold text-[#F5F5F3]">
              {bot.total_pages_indexed.toLocaleString()}
            </p>
            <p className="mt-1 text-xs uppercase tracking-wider text-[#8C9299]">
              Pages indexed
            </p>
          </div>

          <div className="px-6 py-5">
            <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg border border-[#D6A84F]/20 bg-[#D6A84F]/10">
              <Layers3 className="h-4 w-4 text-[#D6A84F]" />
            </div>
            <p className="text-2xl font-bold text-[#F5F5F3]">
              {bot.total_chunks.toLocaleString()}
            </p>
            <p className="mt-1 text-xs uppercase tracking-wider text-[#8C9299]">
              Knowledge chunks
            </p>
          </div>

          <div className="px-6 py-5">
            <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg border border-[#D6A84F]/20 bg-[#D6A84F]/10">
              <Clock className="h-4 w-4 text-[#D6A84F]" />
            </div>
            <p className="text-sm font-semibold text-[#F5F5F3]">
              {new Date(bot.updated_at).toLocaleString()}
            </p>
            <p className="mt-1 text-xs uppercase tracking-wider text-[#8C9299]">
              Last updated
            </p>
          </div>
        </div>
      </section>

      {/* Failed crawl */}
      {bot.status === 'FAILED' && bot.last_error && (
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-5">
          <div className="flex gap-3">
            <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
            <div>
              <p className="font-semibold text-red-300">
                Processing failed
              </p>
              <p className="mt-1 text-sm leading-6 text-red-300/70">
                {bot.last_error}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Refresh warning */}
      {error && bot && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-sm text-amber-300">
          Latest refresh failed: {error}
        </div>
      )}

      {/* Management */}
      <section>
        <div className="mb-4">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
            Manage
          </p>
          <h2 className="mt-1 text-xl font-semibold text-[#F5F5F3]">
            Configure your chatbot
          </h2>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={`/dashboard/bots/${botId}/${item.href}`}
                className="group rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5 transition hover:-translate-y-0.5 hover:border-[#D6A84F]/40 hover:bg-[#15181C]"
              >
                <div className="mb-5 flex items-start justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
                    <Icon className="h-5 w-5 text-[#D6A84F]" />
                  </div>

                  <ChevronRight className="h-5 w-5 text-[#5F656D] transition group-hover:translate-x-1 group-hover:text-[#D6A84F]" />
                </div>

                <h3 className="font-semibold text-[#F5F5F3] transition group-hover:text-[#F0C76A]">
                  {item.label}
                </h3>

                <p className="mt-2 text-sm leading-5 text-[#8C9299]">
                  {item.description}
                </p>
              </Link>
            );
          })}
        </div>
      </section>

      <p className="text-xs text-[#5F656D]">
        Created {new Date(bot.created_at).toLocaleString()}
      </p>
    </div>
  );
}
