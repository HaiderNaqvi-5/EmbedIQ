'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  Bot,
  Database,
  BarChart3,
  Plus,
  ArrowRight,
  Globe,
  CheckCircle2,
  Loader2,
  XCircle,
  Activity,
  AlertCircle,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';

interface BotSummary {
  id: string;
  name: string | null;
  website_url: string;
  status: string;
  created_at: string;
}

const PROCESSING_STATUSES = [
  'PENDING',
  'QUEUED',
  'CRAWLING',
  'PROCESSING',
  'INDEXING',
];

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

export default function DashboardPage() {
  const [bots, setBots] = useState<BotSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<BotSummary[]>('/api/bots')
      .then((data) => {
        setBots(data);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load workspace information.'
        );
      })
      .finally(() => setLoading(false));
  }, []);

  const stats = useMemo(() => {
    const ready = bots.filter((bot) =>
      ['READY', 'READY_WITH_WARNINGS'].includes(bot.status)
    ).length;

    const processing = bots.filter((bot) =>
      PROCESSING_STATUSES.includes(bot.status)
    ).length;

    const failed = bots.filter(
      (bot) => bot.status === 'FAILED'
    ).length;

    return {
      total: bots.length,
      ready,
      processing,
      failed,
    };
  }, [bots]);

  const recentBots = useMemo(
    () =>
      [...bots]
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() -
            new Date(a.created_at).getTime()
        )
        .slice(0, 4),
    [bots]
  );

  const statCards = [
    {
      label: 'Total Bots',
      value: stats.total,
      icon: Bot,
    },
    {
      label: 'Ready',
      value: stats.ready,
      icon: CheckCircle2,
    },
    {
      label: 'Processing',
      value: stats.processing,
      icon: Activity,
    },
    {
      label: 'Failed',
      value: stats.failed,
      icon: XCircle,
    },
  ];

  const actions = [
    {
      title: 'Create New Bot',
      description: 'Turn a website into an AI assistant.',
      href: '/dashboard/bots/new',
      icon: Plus,
      primary: true,
    },
    {
      title: 'Knowledge',
      description: 'Browse your isolated knowledge bases.',
      href: '/dashboard/knowledge',
      icon: Database,
      primary: false,
    },
    {
      title: 'Analytics',
      description: 'View chatbot activity and performance.',
      href: '/dashboard/analytics',
      icon: BarChart3,
      primary: false,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
            Overview
          </p>

          <h1 className="text-3xl font-bold tracking-tight text-[#F5F5F3]">
            Dashboard
          </h1>

          <p className="mt-2 text-[#9EA3AA]">
            Monitor your AI assistants, knowledge bases and workspace activity.
          </p>
        </div>

        <Link
          href="/dashboard/bots/new"
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#D6A84F] px-4 py-2.5 text-sm font-semibold text-[#080A0D] transition hover:bg-[#F0C76A]"
        >
          <Plus className="h-4 w-4" />
          Create Bot
        </Link>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-300">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Statistics */}
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        {statCards.map(({ label, value, icon: Icon }) => (
          <div
            key={label}
            className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5"
          >
            <div className="mb-5 flex items-center justify-between">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#D6A84F]/20 bg-[#D6A84F]/10">
                <Icon className="h-4 w-4 text-[#D6A84F]" />
              </div>
            </div>

            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin text-[#D6A84F]" />
            ) : (
              <p className="text-3xl font-bold text-[#F5F5F3]">
                {value}
              </p>
            )}

            <p className="mt-1 text-sm text-[#8C9299]">
              {label}
            </p>
          </div>
        ))}
      </div>

      {/* Main content */}
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(300px,0.8fr)]">
        {/* Recent bots */}
        <section className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418]">
          <div className="flex items-center justify-between border-b border-[#C8CBD0]/10 px-6 py-5">
            <div>
              <h2 className="font-semibold text-[#F5F5F3]">
                Your Bots
              </h2>

              <p className="mt-1 text-sm text-[#8C9299]">
                Recently created AI assistants.
              </p>
            </div>

            <Link
              href="/dashboard/bots"
              className="flex items-center gap-1 text-sm font-medium text-[#D6A84F] transition hover:text-[#F0C76A]"
            >
              View all
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div>
            {loading && (
              <div className="flex h-56 items-center justify-center">
                <Loader2 className="h-7 w-7 animate-spin text-[#D6A84F]" />
              </div>
            )}

            {!loading && recentBots.length === 0 && (
              <div className="px-6 py-14 text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
                  <Bot className="h-5 w-5 text-[#D6A84F]" />
                </div>

                <h3 className="mt-4 font-semibold text-[#F5F5F3]">
                  No bots yet
                </h3>

                <p className="mt-2 text-sm text-[#8C9299]">
                  Create your first website-specific AI assistant.
                </p>

                <Link
                  href="/dashboard/bots/new"
                  className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#D6A84F] hover:text-[#F0C76A]"
                >
                  Create a bot
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            )}

            {!loading &&
              recentBots.map((bot, index) => (
                <Link
                  key={bot.id}
                  href={`/dashboard/bots/${bot.id}`}
                  className={`group flex items-center gap-4 px-6 py-5 transition hover:bg-[#1A1D21] ${
                    index !== recentBots.length - 1
                      ? 'border-b border-[#C8CBD0]/10'
                      : ''
                  }`}
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
                    <Bot className="h-5 w-5 text-[#D6A84F]" />
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

                  <ArrowRight className="h-4 w-4 shrink-0 text-[#5F656D] transition group-hover:translate-x-1 group-hover:text-[#D6A84F]" />
                </Link>
              ))}
          </div>
        </section>

        {/* Quick actions */}
        <section className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-6">
          <h2 className="font-semibold text-[#F5F5F3]">
            Quick Actions
          </h2>

          <p className="mt-1 text-sm text-[#8C9299]">
            Common workspace tasks.
          </p>

          <div className="mt-5 space-y-3">
            {actions.map((action) => {
              const Icon = action.icon;

              return (
                <Link
                  key={action.title}
                  href={action.href}
                  className={`group flex items-center gap-3 rounded-xl border p-4 transition ${
                    action.primary
                      ? 'border-[#D6A84F]/30 bg-[#D6A84F]/10 hover:border-[#D6A84F]/50'
                      : 'border-[#C8CBD0]/10 bg-[#1A1D21] hover:border-[#D6A84F]/30'
                  }`}
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[#D6A84F]/20 bg-[#D6A84F]/10">
                    <Icon className="h-4 w-4 text-[#D6A84F]" />
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-[#F5F5F3]">
                      {action.title}
                    </p>

                    <p className="mt-0.5 text-xs leading-5 text-[#8C9299]">
                      {action.description}
                    </p>
                  </div>

                  <ArrowRight className="h-4 w-4 text-[#5F656D] transition group-hover:translate-x-1 group-hover:text-[#D6A84F]" />
                </Link>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
