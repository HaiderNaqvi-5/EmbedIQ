'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { apiRequest } from '@/lib/api';
import {
  Loader2,
  FileText,
  Hash,
  Clock,
  ChevronLeft,
  Database,
} from 'lucide-react';

interface KnowledgeData {
  bot_id: string;
  document_id: string | null;
  markdown_content: string | null;
  chunk_count: number;
  last_indexed_at: string | null;
}

export default function KnowledgePage() {
  const params = useParams();
  const botId = params.bot_id as string;

  const [knowledge, setKnowledge] = useState<KnowledgeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<KnowledgeData>(`/api/bots/${botId}/knowledge`)
      .then(setKnowledge)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : 'Failed to load knowledge.')
      )
      .finally(() => setLoading(false));
  }, [botId]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#D6A84F]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-5 text-sm text-red-300">
        {error}
      </div>
    );
  }

  if (!knowledge) return null;

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
          Knowledge
        </p>

        <h1 className="mt-2 text-2xl font-bold text-[#F5F5F3]">
          Knowledge Base
        </h1>

        <p className="mt-2 text-sm text-[#8C9299]">
          Inspect the canonical website knowledge used by this chatbot.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5">
          <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg border border-[#D6A84F]/20 bg-[#D6A84F]/10">
            <Hash className="h-4 w-4 text-[#D6A84F]" />
          </div>

          <p className="text-3xl font-bold text-[#F5F5F3]">
            {knowledge.chunk_count.toLocaleString()}
          </p>

          <p className="mt-1 text-sm text-[#8C9299]">
            Indexed chunks
          </p>
        </div>

        <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5">
          <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg border border-[#D6A84F]/20 bg-[#D6A84F]/10">
            <Clock className="h-4 w-4 text-[#D6A84F]" />
          </div>

          <p className="text-sm font-semibold text-[#F5F5F3]">
            {knowledge.last_indexed_at
              ? new Date(knowledge.last_indexed_at).toLocaleString()
              : 'Never'}
          </p>

          <p className="mt-1 text-sm text-[#8C9299]">
            Last indexed
          </p>
        </div>
      </div>

      {knowledge.markdown_content ? (
        <section className="overflow-hidden rounded-2xl border border-[#C8CBD0]/10 bg-[#111418]">
          <div className="flex flex-col justify-between gap-3 border-b border-[#C8CBD0]/10 px-5 py-4 sm:flex-row sm:items-center">
            <div className="flex items-center gap-3">
              <FileText className="h-4 w-4 text-[#D6A84F]" />

              <div>
                <p className="text-sm font-semibold text-[#F5F5F3]">
                  website.md
                </p>
                <p className="text-xs text-[#8C9299]">
                  Canonical knowledge base
                </p>
              </div>
            </div>

            <span className="text-xs text-[#5F656D]">
              {knowledge.markdown_content.length.toLocaleString()} characters
            </span>
          </div>

          <div className="max-h-[650px] overflow-auto bg-[#0D1013] p-5">
            <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-6 text-[#C8CBD0]">
              {knowledge.markdown_content}
            </pre>
          </div>
        </section>
      ) : (
        <section className="rounded-2xl border border-dashed border-[#C8CBD0]/15 bg-[#111418] px-6 py-16 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
            <Database className="h-5 w-5 text-[#D6A84F]" />
          </div>

          <h2 className="mt-4 font-semibold text-[#F5F5F3]">
            No knowledge base yet
          </h2>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[#8C9299]">
            The canonical knowledge base will appear here once website processing
            and indexing have completed.
          </p>
        </section>
      )}
    </div>
  );
}
