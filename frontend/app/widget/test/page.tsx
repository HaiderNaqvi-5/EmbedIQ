"use client";

import {
  FormEvent,
  Suspense,
  useEffect,
  useState,
} from "react";
import { useSearchParams } from "next/navigation";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function WidgetTestContent() {
  const searchParams = useSearchParams();
  const queryBotId = searchParams.get("bot_id") || "";

  const [botId, setBotId] = useState(queryBotId);
  const [loadedBotId, setLoadedBotId] = useState(queryBotId);

  useEffect(() => {
    if (queryBotId) {
      setBotId(queryBotId);
      setLoadedBotId(queryBotId);
    }
  }, [queryBotId]);

  useEffect(() => {
    if (!loadedBotId) return;

    document.getElementById("embediq-host")?.remove();
    document.getElementById("embediq-widget-script")?.remove();

    const script = document.createElement("script");

    script.id = "embediq-widget-script";
    script.src = "/widget.js";
    script.async = true;

    script.setAttribute("data-bot-id", loadedBotId);
    script.setAttribute("data-api-url", API_URL);
    script.setAttribute("data-base-url", window.location.origin);
    script.setAttribute("data-position", "bottom-right");

    script.onload = () => {
      console.log("[EmbedIQ Test] widget.js loaded");
    };

    script.onerror = (error) => {
      console.error("[EmbedIQ Test] widget.js failed", error);
    };

    document.body.appendChild(script);

    return () => {
      document.getElementById("embediq-host")?.remove();
      document.getElementById("embediq-widget-script")?.remove();
    };
  }, [loadedBotId]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const cleanBotId = botId.trim();
    if (!cleanBotId) return;

    setLoadedBotId("");

    setTimeout(() => {
      setLoadedBotId(cleanBotId);
    }, 0);

    const url = new URL(window.location.href);
    url.searchParams.set("bot_id", cleanBotId);
    window.history.replaceState({}, "", url.toString());
  }

  return (
    <main className="min-h-screen bg-[#080A0D] px-6 py-12 text-[#F5F5F3]">
      <div className="mx-auto max-w-3xl space-y-8">
        <section className="rounded-2xl border border-[#2A2E34] bg-[#111418] p-8 shadow-xl">
          <div className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
            EmbedIQ
          </div>

          <h1 className="text-3xl font-bold">
            Widget Test
          </h1>

          <p className="mt-4 text-[#9EA3AA]">
            Enter a Bot ID to load the chatbot widget on this page.
          </p>

          <form
            onSubmit={handleSubmit}
            className="mt-6 flex flex-col gap-3 sm:flex-row"
          >
            <input
              value={botId}
              onChange={(event) => setBotId(event.target.value)}
              placeholder="Enter Bot ID"
              className="flex-1 rounded-xl border border-[#34383E] bg-[#1A1D21] px-4 py-3 text-[#F5F5F3] outline-none placeholder:text-[#8C9299] focus:border-[#D6A84F]"
            />

            <button
              type="submit"
              className="rounded-xl bg-[#D6A84F] px-6 py-3 font-semibold text-[#080A0D] transition hover:bg-[#F0C76A]"
            >
              Load Widget
            </button>
          </form>

          {loadedBotId && (
            <p className="mt-4 text-sm font-medium text-[#F0C76A]">
              ✓ Widget loaded for bot: {loadedBotId}
            </p>
          )}
        </section>

        <section className="rounded-2xl border border-[#2A2E34] bg-[#111418] p-8">
          <h2 className="text-2xl font-bold">
            Widget Preview Environment
          </h2>

          <p className="mt-5 text-[#9EA3AA]">
            This page simulates a customer website so you can verify the
            floating EmbedIQ chatbot, branding, logo, and conversation flow.
          </p>
        </section>
      </div>
    </main>
  );
}

export default function WidgetTestPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center bg-[#080A0D] text-[#F5F5F3]">
          Loading widget test…
        </main>
      }
    >
      <WidgetTestContent />
    </Suspense>
  );
}
