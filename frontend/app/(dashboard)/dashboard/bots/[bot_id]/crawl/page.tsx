'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { apiRequest } from '@/lib/api';
import {
  Loader2, CheckCircle2, XCircle, AlertCircle, Clock,
  Globe, FileSearch, Database, ChevronLeft, Activity
} from 'lucide-react';

interface CrawlStatus {
  bot_id: string;
  job_id: string | null;
  status: string;
  stage: string;
  total_pages: number;
  processed_pages: number;
  failed_pages: number;
  warning_count: number;
  error_code: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

const STAGES = [
  'VALIDATING',
  'DISCOVERING',
  'CRAWLING',
  'EXTRACTING',
  'BRANDING',
  'GENERATING_KNOWLEDGE',
  'CHUNKING',
  'EMBEDDING',
  'INDEXING',
  'COMPLETED',
];

const LABELS: Record<string, string> = {
  VALIDATING: 'Validating URL',
  DISCOVERING: 'Discovering pages',
  CRAWLING: 'Crawling website',
  EXTRACTING: 'Extracting content',
  BRANDING: 'Extracting branding',
  GENERATING_KNOWLEDGE: 'Building knowledge base',
  CHUNKING: 'Chunking content',
  EMBEDDING: 'Generating embeddings',
  INDEXING: 'Indexing vectors',
  COMPLETED: 'Completed',
};

function Stage({
  stage,
  currentStage,
  status,
}: {
  stage: string;
  currentStage: string;
  status: string;
}) {
  const index = STAGES.indexOf(stage);
  const current = STAGES.indexOf(currentStage);
  const active = stage === currentStage;
  const done =
    status === 'COMPLETED' ||
    current > index ||
    currentStage === 'COMPLETED';
  const failed = status === 'FAILED' && active;

  return (
    <div
      className={`flex items-center gap-3 rounded-xl border px-4 py-3 transition ${
        active
          ? 'border-[#D6A84F]/35 bg-[#D6A84F]/8'
          : 'border-transparent'
      }`}
    >
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${
          failed
            ? 'border-red-500/30 bg-red-500/10 text-red-300'
            : done
            ? 'border-emerald-500/25 bg-emerald-500/10 text-emerald-300'
            : active
            ? 'border-[#D6A84F]/40 bg-[#D6A84F]/10 text-[#F0C76A]'
            : 'border-[#C8CBD0]/10 bg-[#1A1D21] text-[#5F656D]'
        }`}
      >
        {failed ? (
          <XCircle className="h-4 w-4" />
        ) : done ? (
          <CheckCircle2 className="h-4 w-4" />
        ) : active ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <span className="text-xs font-semibold">{index + 1}</span>
        )}
      </div>

      <span
        className={`text-sm font-medium ${
          failed
            ? 'text-red-300'
            : done
            ? 'text-emerald-300'
            : active
            ? 'text-[#F0C76A]'
            : 'text-[#8C9299]'
        }`}
      >
        {LABELS[stage] || stage}
      </span>
    </div>
  );
}

export default function CrawlProgressPage() {
  const params = useParams();
  const botId = params.bot_id as string;

  const [crawlStatus, setCrawlStatus] = useState<CrawlStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await apiRequest<CrawlStatus>(
        `/api/bots/${botId}/crawl/status`
      );
      setCrawlStatus(data);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load crawl status.');
    } finally {
      setLoading(false);
    }
  }, [botId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    if (
      !crawlStatus ||
      ['COMPLETED', 'FAILED'].includes(crawlStatus.status)
    ) return;

    const interval = window.setInterval(fetchStatus, 3000);
    return () => window.clearInterval(interval);
  }, [crawlStatus?.status, fetchStatus]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#D6A84F]" />
      </div>
    );
  }

  if (error && !crawlStatus) {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-5 text-sm text-red-300">
        {error}
      </div>
    );
  }

  if (!crawlStatus) return null;

  const terminal = ['COMPLETED', 'FAILED'].includes(crawlStatus.status);

  const progress =
    crawlStatus.total_pages > 0
      ? Math.min(
          100,
          Math.round(
            (crawlStatus.processed_pages / crawlStatus.total_pages) * 100
          )
        )
      : 0;

  const stats = [
    { label: 'Total Pages', value: crawlStatus.total_pages, icon: Globe },
    { label: 'Processed', value: crawlStatus.processed_pages, icon: FileSearch },
    { label: 'Failed', value: crawlStatus.failed_pages, icon: XCircle },
    { label: 'Warnings', value: crawlStatus.warning_count, icon: AlertCircle },
  ];

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

        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
              Processing
            </p>
            <h1 className="mt-2 text-2xl font-bold text-[#F5F5F3]">
              Crawl Progress
            </h1>
            <p className="mt-2 text-sm text-[#8C9299]">
              Follow your website through the EmbedIQ ingestion pipeline.
            </p>
          </div>

          {!terminal && (
            <div className="inline-flex items-center gap-2 text-xs font-medium text-[#D6A84F]">
              <Loader2 className="h-4 w-4 animate-spin" />
              Auto-refreshing
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        {stats.map(({ label, value, icon: Icon }) => (
          <div
            key={label}
            className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5"
          >
            <Icon className="mb-4 h-4 w-4 text-[#D6A84F]" />
            <p className="text-2xl font-bold text-[#F5F5F3]">{value}</p>
            <p className="mt-1 text-xs uppercase tracking-wider text-[#8C9299]">
              {label}
            </p>
          </div>
        ))}
      </div>

      <section className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-6">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-[#F5F5F3]">
              Website processing
            </h2>
            <p className="mt-1 text-sm text-[#8C9299]">
              {crawlStatus.processed_pages} of {crawlStatus.total_pages} pages processed
            </p>
          </div>

          <span className="text-xl font-bold text-[#F0C76A]">
            {progress}%
          </span>
        </div>

        <div className="h-2 overflow-hidden rounded-full bg-[#1A1D21]">
          <div
            className="h-full rounded-full bg-[#D6A84F] transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="mt-4 flex items-center gap-2 text-xs text-[#8C9299]">
          <Activity className="h-3.5 w-3.5" />
          Current stage:
          <span className="font-medium text-[#C8CBD0]">
            {LABELS[crawlStatus.stage] || crawlStatus.stage}
          </span>
        </div>
      </section>

      {crawlStatus.error_message && (
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-5">
          <div className="flex gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
            <div>
              <p className="font-semibold text-red-300">
                {crawlStatus.error_code || 'Crawl error'}
              </p>
              <p className="mt-1 text-sm text-red-300/70">
                {crawlStatus.error_message}
              </p>
            </div>
          </div>
        </div>
      )}

      <section className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-6">
        <div className="mb-5 flex items-center gap-3">
          <Database className="h-5 w-5 text-[#D6A84F]" />
          <div>
            <h2 className="font-semibold text-[#F5F5F3]">
              Ingestion Pipeline
            </h2>
            <p className="mt-0.5 text-sm text-[#8C9299]">
              Crawl, extraction, knowledge generation and indexing.
            </p>
          </div>
        </div>

        <div className="grid gap-1 lg:grid-cols-2">
          {STAGES.map((stage) => (
            <Stage
              key={stage}
              stage={stage}
              currentStage={crawlStatus.stage}
              status={crawlStatus.status}
            />
          ))}
        </div>
      </section>

      {crawlStatus.started_at && (
        <div className="flex items-center gap-2 text-xs text-[#5F656D]">
          <Clock className="h-3.5 w-3.5" />
          Started {new Date(crawlStatus.started_at).toLocaleString()}
          {crawlStatus.completed_at &&
            ` · Completed ${new Date(crawlStatus.completed_at).toLocaleString()}`}
        </div>
      )}
    </div>
  );
}
