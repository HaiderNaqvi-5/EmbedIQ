'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Globe,
  ArrowLeft,
  Loader2,
  AlertCircle,
  Bot,
  Sparkles,
  Database,
  Braces,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';

interface CreateBotResponse {
  bot_id: string;
  job_id: string;
  name: string;
  website_url: string;
  status: string;
  created_at: string;
}

function isValidUrl(value: string): boolean {
  try {
    const url = new URL(value);

    return (
      (url.protocol === 'http:' || url.protocol === 'https:') &&
      Boolean(url.hostname)
    );
  } catch {
    return false;
  }
}

export default function NewBotPage() {
  const router = useRouter();

  const [websiteUrl, setWebsiteUrl] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    const cleanUrl = websiteUrl.trim();

    if (!isValidUrl(cleanUrl)) {
      setError(
        'Enter a valid public website URL beginning with http:// or https://.'
      );
      return;
    }

    setLoading(true);

    try {
      const bot = await apiRequest<CreateBotResponse>(
        '/api/bots',
        {
          method: 'POST',
          body: JSON.stringify({
            website_url: cleanUrl,
            ...(name.trim()
              ? { name: name.trim() }
              : {}),
          }),
        }
      );

      router.push(`/dashboard/bots/${bot.bot_id}`);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to create bot. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <Link
        href="/dashboard/bots"
        className="inline-flex items-center gap-2 text-sm text-[#8C9299] transition hover:text-[#F0C76A]"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to My Bots
      </Link>

      <div>
        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
          New Chatbot
        </p>

        <h1 className="text-3xl font-bold tracking-tight text-[#F5F5F3]">
          Create a Website Assistant
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-[#9EA3AA]">
          Give EmbedIQ a public website and it will build an
          isolated, embeddable AI knowledge assistant for that site.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-6 sm:p-8">
          <div className="mb-7 flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
              <Bot className="h-6 w-6 text-[#D6A84F]" />
            </div>

            <div>
              <h2 className="font-semibold text-[#F5F5F3]">
                Bot Details
              </h2>

              <p className="mt-1 text-sm text-[#8C9299]">
                Start with the website you want EmbedIQ to learn.
              </p>
            </div>
          </div>

          {error && (
            <div className="mb-6 flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-300">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form
            onSubmit={handleSubmit}
            className="space-y-6"
          >
            <div>
              <label
                htmlFor="website-url"
                className="mb-2 block text-sm font-medium text-[#C8CBD0]"
              >
                Website URL
                <span className="ml-1 text-[#D6A84F]">*</span>
              </label>

              <div className="relative">
                <Globe className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#5F656D]" />

                <input
                  id="website-url"
                  type="url"
                  required
                  autoFocus
                  value={websiteUrl}
                  onChange={(event) =>
                    setWebsiteUrl(event.target.value)
                  }
                  placeholder="https://yourwebsite.com"
                  className="w-full rounded-xl border border-[#C8CBD0]/10 bg-[#080A0D] py-3 pl-10 pr-4 text-sm text-[#F5F5F3] outline-none transition placeholder:text-[#5F656D] focus:border-[#D6A84F]/50 focus:ring-2 focus:ring-[#D6A84F]/10"
                />
              </div>

              <p className="mt-2 text-xs leading-5 text-[#5F656D]">
                Use a publicly accessible HTTP or HTTPS website.
                Private and internal addresses are blocked.
              </p>
            </div>

            <div>
              <label
                htmlFor="bot-name"
                className="mb-2 block text-sm font-medium text-[#C8CBD0]"
              >
                Bot Name
                <span className="ml-2 font-normal text-[#5F656D]">
                  optional
                </span>
              </label>

              <input
                id="bot-name"
                type="text"
                value={name}
                onChange={(event) =>
                  setName(event.target.value)
                }
                maxLength={100}
                placeholder="e.g. Acme Support Assistant"
                className="w-full rounded-xl border border-[#C8CBD0]/10 bg-[#080A0D] px-4 py-3 text-sm text-[#F5F5F3] outline-none transition placeholder:text-[#5F656D] focus:border-[#D6A84F]/50 focus:ring-2 focus:ring-[#D6A84F]/10"
              />

              <p className="mt-2 text-xs leading-5 text-[#5F656D]">
                Leave this blank and EmbedIQ will derive a name
                automatically from the website.
              </p>
            </div>

            <div className="rounded-xl border border-[#D6A84F]/15 bg-[#D6A84F]/5 p-4">
              <div className="flex gap-3">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[#D6A84F]" />

                <div>
                  <p className="text-sm font-medium text-[#E8EAEC]">
                    Isolated knowledge
                  </p>

                  <p className="mt-1 text-xs leading-5 text-[#8C9299]">
                    Every chatbot gets its own bot-scoped website
                    content, chunks and vector knowledge base.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col-reverse gap-3 border-t border-[#C8CBD0]/10 pt-6 sm:flex-row sm:justify-end">
              <Link
                href="/dashboard/bots"
                className="inline-flex items-center justify-center rounded-xl border border-[#C8CBD0]/10 px-5 py-3 text-sm font-medium text-[#C8CBD0] transition hover:border-[#C8CBD0]/20 hover:bg-[#1A1D21]"
              >
                Cancel
              </Link>

              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#D6A84F] px-5 py-3 text-sm font-semibold text-[#080A0D] transition hover:bg-[#F0C76A] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#D6A84F]/50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating Bot...
                  </>
                ) : (
                  <>
                    Create Bot & Start Crawl
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </section>

        <aside className="space-y-4">
          <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
              <Sparkles className="h-5 w-5 text-[#D6A84F]" />
            </div>

            <h2 className="mt-5 font-semibold text-[#F5F5F3]">
              What happens next?
            </h2>

            <p className="mt-2 text-sm leading-6 text-[#8C9299]">
              EmbedIQ automatically processes the website and
              prepares it for grounded chatbot responses.
            </p>
          </div>

          {[
            {
              step: '01',
              title: 'Crawl website',
              description:
                'Discover and extract accessible website pages.',
              icon: Globe,
            },
            {
              step: '02',
              title: 'Build knowledge',
              description:
                'Clean the content and generate canonical Markdown.',
              icon: Database,
            },
            {
              step: '03',
              title: 'Index embeddings',
              description:
                'Create searchable vector chunks for retrieval.',
              icon: Braces,
            },
            {
              step: '04',
              title: 'Embed anywhere',
              description:
                'Use the generated widget snippet on your website.',
              icon: Bot,
            },
          ].map(
            ({
              step,
              title,
              description,
              icon: Icon,
            }) => (
              <div
                key={step}
                className="flex gap-4 rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-4"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[#C8CBD0]/10 bg-[#1A1D21]">
                  <Icon className="h-4 w-4 text-[#D6A84F]" />
                </div>

                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-semibold tracking-[0.15em] text-[#D6A84F]">
                      {step}
                    </span>

                    <p className="text-sm font-medium text-[#E8EAEC]">
                      {title}
                    </p>
                  </div>

                  <p className="mt-1 text-xs leading-5 text-[#8C9299]">
                    {description}
                  </p>
                </div>
              </div>
            )
          )}
        </aside>
      </div>
    </div>
  );
}
