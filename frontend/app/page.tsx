import Link from 'next/link';
import {
  Bot,
  ArrowRight,
  ShieldCheck,
  Zap,
  Sparkles,
  Database,
  Code2,
} from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#080A0D] text-[#F5F5F3]">
      <header className="sticky top-0 z-50 border-b border-[#C8CBD0]/10 bg-[#080A0D]/90 backdrop-blur-xl">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 sm:px-8">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#D6A84F]/30 bg-[#D6A84F]/10 text-[#F0C76A]">
              <Sparkles className="h-5 w-5" />
            </div>

            <span className="text-xl font-bold tracking-tight">
              Embed<span className="text-[#D6A84F]">IQ</span>
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-[#C8CBD0] transition hover:text-[#F5F5F3]"
            >
              Sign In
            </Link>

            <Link
              href="/register"
              className="rounded-xl bg-[#D6A84F] px-5 py-2.5 text-sm font-semibold text-[#080A0D] transition hover:bg-[#F0C76A]"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden border-b border-[#C8CBD0]/10">
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute left-1/2 top-20 h-[520px] w-[520px] -translate-x-1/2 rounded-full bg-[#D6A84F]/5 blur-3xl" />
          </div>

          <div className="relative mx-auto max-w-6xl px-5 py-24 text-center sm:px-8 sm:py-32">
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-[#D6A84F]/25 bg-[#D6A84F]/8 px-4 py-2 text-xs font-semibold uppercase tracking-[0.15em] text-[#F0C76A]">
              <Sparkles className="h-3.5 w-3.5" />
              Website-Specific RAG Platform
            </div>

            <h1 className="mx-auto max-w-5xl text-5xl font-extrabold leading-[1.05] tracking-tight sm:text-7xl">
              Turn any website into a{' '}
              <span className="text-[#D6A84F]">
                grounded AI assistant
              </span>
              .
            </h1>

            <p className="mx-auto mt-7 max-w-3xl text-lg leading-8 text-[#9EA3AA] sm:text-xl">
              Crawl your website, build an isolated knowledge base and deploy
              an embeddable AI chatbot that answers from your content.
            </p>

            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/register"
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#D6A84F] px-7 py-3.5 font-semibold text-[#080A0D] transition hover:bg-[#F0C76A] sm:w-auto"
              >
                Create Your Chatbot
                <ArrowRight className="h-4 w-4" />
              </Link>

              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-[#34383E] bg-[#111418] px-7 py-3.5 font-semibold text-[#C8CBD0] transition hover:border-[#D6A84F]/50 hover:text-[#F5F5F3] sm:w-auto"
              >
                Explore API
                <Code2 className="h-4 w-4" />
              </a>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-5 py-20 sm:px-8">
          <div className="mb-10">
            <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
              Built for reliable website AI
            </p>

            <h2 className="text-3xl font-bold">
              Simple. Powerful. Embeddable.
            </h2>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            <Feature
              icon={Zap}
              title="Dual-Mode Crawling"
              description="Fast HTTP crawling with Playwright fallback for modern JavaScript-powered websites."
            />

            <Feature
              icon={ShieldCheck}
              title="Tenant Isolation"
              description="Every bot uses its own website-scoped knowledge and retrieval boundary."
            />

            <Feature
              icon={Bot}
              title="Embeddable Widget"
              description="Deploy a lightweight chatbot widget to your website using a simple script snippet."
            />
          </div>
        </section>

        <section className="border-y border-[#C8CBD0]/10 bg-[#111418]">
          <div className="mx-auto grid max-w-7xl gap-8 px-5 py-20 sm:px-8 lg:grid-cols-2">
            <div>
              <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
                Knowledge Pipeline
              </p>

              <h2 className="max-w-xl text-4xl font-bold leading-tight">
                From website URL to searchable knowledge.
              </h2>

              <p className="mt-5 max-w-xl leading-7 text-[#9EA3AA]">
                EmbedIQ discovers pages, extracts useful content, generates
                chunks and embeddings and stores everything inside a
                bot-isolated pgvector knowledge base.
              </p>
            </div>

            <div className="rounded-2xl border border-[#2A2E34] bg-[#1A1D21] p-7">
              <div className="flex items-center gap-3 border-b border-[#C8CBD0]/10 pb-5">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#D6A84F]/10 text-[#D6A84F]">
                  <Database className="h-5 w-5" />
                </div>

                <div>
                  <div className="font-semibold">Bot-scoped RAG</div>
                  <div className="text-sm text-[#8C9299]">
                    Website-specific retrieval
                  </div>
                </div>
              </div>

              <div className="space-y-4 pt-5 text-sm text-[#C8CBD0]">
                <PipelineStep number="01" text="Discover and crawl website pages" />
                <PipelineStep number="02" text="Extract content and branding" />
                <PipelineStep number="03" text="Chunk and generate embeddings" />
                <PipelineStep number="04" text="Store vectors with bot isolation" />
                <PipelineStep number="05" text="Answer with retrieved website knowledge" />
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-5xl px-5 py-24 text-center sm:px-8">
          <h2 className="text-4xl font-bold">
            Build your website assistant.
          </h2>

          <p className="mx-auto mt-4 max-w-xl text-[#9EA3AA]">
            Create a bot, crawl your website and deploy your chatbot from one workspace.
          </p>

          <Link
            href="/register"
            className="mt-8 inline-flex items-center gap-2 rounded-xl bg-[#D6A84F] px-7 py-3.5 font-semibold text-[#080A0D] transition hover:bg-[#F0C76A]"
          >
            Get Started
            <ArrowRight className="h-4 w-4" />
          </Link>
        </section>
      </main>

      <footer className="border-t border-[#C8CBD0]/10 bg-[#0D1014]">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-7 text-sm text-[#8C9299] sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <div>
            Embed<span className="text-[#D6A84F]">IQ</span>
          </div>

          <div>
            Website-specific RAG chatbot platform
          </div>
        </div>
      </footer>
    </div>
  );
}

function Feature({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof Zap;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-[#2A2E34] bg-[#111418] p-7 transition hover:border-[#D6A84F]/40">
      <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl border border-[#D6A84F]/25 bg-[#D6A84F]/8 text-[#D6A84F]">
        <Icon className="h-5 w-5" />
      </div>

      <h3 className="text-lg font-semibold">
        {title}
      </h3>

      <p className="mt-2 leading-6 text-[#9EA3AA]">
        {description}
      </p>
    </div>
  );
}

function PipelineStep({
  number,
  text,
}: {
  number: string;
  text: string;
}) {
  return (
    <div className="flex items-center gap-4">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-[#D6A84F]/25 bg-[#D6A84F]/8 text-xs font-bold text-[#D6A84F]">
        {number}
      </div>

      <span>{text}</span>
    </div>
  );
}
