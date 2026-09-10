'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  Activity,
  Bot,
  MessageSquare,
  MessagesSquare,
  UserRound,
  Loader2,
  AlertCircle,
  ArrowRight,
  CalendarDays,
  BarChart3,
  Clock3,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';

interface AnalyticsSummary {
  total_bots: number;
  active_bots: number;
  total_conversations: number;
  total_messages: number;
  user_questions: number;
  assistant_responses: number;
  conversations_today: number;
  messages_today: number;
  average_messages_per_conversation: number;
}

interface ActivityPoint {
  date: string;
  conversations: number;
  messages: number;
}

interface BotAnalytics {
  bot_id: string;
  bot_name: string;
  website_url: string;
  status: string;
  conversations: number;
  messages: number;
  last_activity: string | null;
}

interface RecentConversation {
  conversation_id: string;
  bot_id: string;
  bot_name: string;
  session_id: string;
  created_at: string;
  last_activity: string | null;
  message_count: number;
}

interface AnalyticsResponse {
  summary: AnalyticsSummary;
  activity: ActivityPoint[];
  bots: BotAnalytics[];
  recent_conversations: RecentConversation[];
}

function formatDate(value: string | null) {
  if (!value) return 'No activity';

  return new Date(value).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
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

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<AnalyticsResponse>('/api/analytics')
      .then((response) => {
        setData(response);
        setError(null);
      })
      .catch((err: unknown) =>
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load analytics.'
        )
      )
      .finally(() => setLoading(false));
  }, []);

  const maxActivity = useMemo(() => {
    if (!data) return 1;

    return Math.max(
      1,
      ...data.activity.flatMap((point) => [
        point.messages,
        point.conversations,
      ])
    );
  }, [data]);

  if (loading) {
    return (
      <div className="flex min-h-[450px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#D6A84F]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-5 text-sm text-red-300">
        <div className="flex gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <p className="font-semibold">Analytics unavailable</p>
            <p className="mt-1 text-red-300/70">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const summaryCards = [
    {
      label: 'Conversations',
      value: data.summary.total_conversations,
      detail: `${data.summary.conversations_today} today`,
      icon: MessagesSquare,
    },
    {
      label: 'Messages',
      value: data.summary.total_messages,
      detail: `${data.summary.messages_today} today`,
      icon: MessageSquare,
    },
    {
      label: 'User Questions',
      value: data.summary.user_questions,
      detail: 'Visitor messages',
      icon: UserRound,
    },
    {
      label: 'Assistant Replies',
      value: data.summary.assistant_responses,
      detail: 'Generated responses',
      icon: Bot,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
          Analytics
        </p>

        <h1 className="text-3xl font-bold tracking-tight text-[#F5F5F3]">
          Conversation Analytics
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-[#9EA3AA]">
          Real usage statistics calculated from your persisted chatbot
          conversations and messages.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        {summaryCards.map(
          ({ label, value, detail, icon: Icon }) => (
            <div
              key={label}
              className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5"
            >
              <div className="mb-5 flex h-9 w-9 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
                <Icon className="h-4 w-4 text-[#D6A84F]" />
              </div>

              <p className="text-3xl font-bold text-[#F5F5F3]">
                {value.toLocaleString()}
              </p>

              <p className="mt-1 text-sm font-medium text-[#C8CBD0]">
                {label}
              </p>

              <p className="mt-1 text-xs text-[#5F656D]">
                {detail}
              </p>
            </div>
          )
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5">
          <Activity className="mb-4 h-4 w-4 text-[#D6A84F]" />

          <p className="text-2xl font-bold text-[#F5F5F3]">
            {data.summary.active_bots}
          </p>

          <p className="mt-1 text-sm text-[#8C9299]">
            Bots with conversations
          </p>
        </div>

        <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5">
          <BarChart3 className="mb-4 h-4 w-4 text-[#D6A84F]" />

          <p className="text-2xl font-bold text-[#F5F5F3]">
            {data.summary.average_messages_per_conversation}
          </p>

          <p className="mt-1 text-sm text-[#8C9299]">
            Avg. messages / conversation
          </p>
        </div>

        <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5">
          <Bot className="mb-4 h-4 w-4 text-[#D6A84F]" />

          <p className="text-2xl font-bold text-[#F5F5F3]">
            {data.summary.total_bots}
          </p>

          <p className="mt-1 text-sm text-[#8C9299]">
            Total bots
          </p>
        </div>
      </div>

      <section className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-6">
        <div className="mb-7">
          <div className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-[#D6A84F]" />
            <h2 className="font-semibold text-[#F5F5F3]">
              Last 7 Days
            </h2>
          </div>

          <p className="mt-1 text-sm text-[#8C9299]">
            Daily conversations and messages.
          </p>
        </div>

        <div className="grid h-56 grid-cols-7 items-end gap-2 sm:gap-4">
          {data.activity.map((point) => {
            const messageHeight =
              (point.messages / maxActivity) * 100;

            const conversationHeight =
              (point.conversations / maxActivity) * 100;

            return (
              <div
                key={point.date}
                className="flex h-full min-w-0 flex-col justify-end"
              >
                <div className="flex h-[180px] items-end justify-center gap-1">
                  <div
                    title={`${point.conversations} conversations`}
                    className="w-2.5 rounded-t bg-[#9C7229] sm:w-4"
                    style={{
                      height: `${Math.max(
                        point.conversations ? 5 : 0,
                        conversationHeight
                      )}%`,
                    }}
                  />

                  <div
                    title={`${point.messages} messages`}
                    className="w-2.5 rounded-t bg-[#D6A84F] sm:w-4"
                    style={{
                      height: `${Math.max(
                        point.messages ? 5 : 0,
                        messageHeight
                      )}%`,
                    }}
                  />
                </div>

                <p className="mt-3 truncate text-center text-[10px] text-[#5F656D] sm:text-xs">
                  {new Date(
                    `${point.date}T00:00:00`
                  ).toLocaleDateString(undefined, {
                    weekday: 'short',
                  })}
                </p>
              </div>
            );
          })}
        </div>

        <div className="mt-5 flex gap-5 border-t border-[#C8CBD0]/10 pt-4 text-xs text-[#8C9299]">
          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-sm bg-[#9C7229]" />
            Conversations
          </span>

          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-sm bg-[#D6A84F]" />
            Messages
          </span>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <section className="overflow-hidden rounded-2xl border border-[#C8CBD0]/10 bg-[#111418]">
          <div className="border-b border-[#C8CBD0]/10 px-6 py-5">
            <h2 className="font-semibold text-[#F5F5F3]">
              Bot Performance
            </h2>

            <p className="mt-1 text-sm text-[#8C9299]">
              Conversation activity for each chatbot.
            </p>
          </div>

          {data.bots.length === 0 ? (
            <div className="px-6 py-12 text-center text-sm text-[#8C9299]">
              No bots yet.
            </div>
          ) : (
            <div>
              {data.bots.map((bot, index) => (
                <Link
                  key={bot.bot_id}
                  href={`/dashboard/bots/${bot.bot_id}`}
                  className={`group flex items-center gap-4 px-6 py-4 transition hover:bg-[#1A1D21] ${
                    index !== data.bots.length - 1
                      ? 'border-b border-[#C8CBD0]/10'
                      : ''
                  }`}
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
                    <Bot className="h-4 w-4 text-[#D6A84F]" />
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-[#F5F5F3] group-hover:text-[#F0C76A]">
                      {bot.bot_name || 'Untitled Bot'}
                    </p>

                    <p className="mt-1 truncate text-xs text-[#5F656D]">
                      {bot.website_url}
                    </p>
                  </div>

                  <div className="hidden text-right sm:block">
                    <p className="text-sm font-semibold text-[#C8CBD0]">
                      {bot.conversations}
                    </p>
                    <p className="text-xs text-[#5F656D]">
                      conversations
                    </p>
                  </div>

                  <div className="hidden text-right md:block">
                    <p className="text-sm font-semibold text-[#C8CBD0]">
                      {bot.messages}
                    </p>
                    <p className="text-xs text-[#5F656D]">
                      messages
                    </p>
                  </div>

                  <span
                    className={`hidden rounded-full border px-2 py-1 text-[10px] font-semibold lg:inline-flex ${statusClasses(
                      bot.status
                    )}`}
                  >
                    {bot.status.replaceAll('_', ' ')}
                  </span>

                  <ArrowRight className="h-4 w-4 shrink-0 text-[#5F656D] transition group-hover:translate-x-1 group-hover:text-[#D6A84F]" />
                </Link>
              ))}
            </div>
          )}
        </section>

        <section className="overflow-hidden rounded-2xl border border-[#C8CBD0]/10 bg-[#111418]">
          <div className="border-b border-[#C8CBD0]/10 px-6 py-5">
            <h2 className="font-semibold text-[#F5F5F3]">
              Recent Conversations
            </h2>

            <p className="mt-1 text-sm text-[#8C9299]">
              Latest visitor sessions across your bots.
            </p>
          </div>

          {data.recent_conversations.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <MessagesSquare className="mx-auto h-6 w-6 text-[#5F656D]" />

              <p className="mt-3 text-sm font-medium text-[#C8CBD0]">
                No conversations yet
              </p>

              <p className="mt-1 text-xs text-[#5F656D]">
                Widget conversations will appear here.
              </p>
            </div>
          ) : (
            <div>
              {data.recent_conversations.map(
                (conversation, index) => (
                  <Link
                    key={conversation.conversation_id}
                    href={`/dashboard/bots/${conversation.bot_id}`}
                    className={`group block px-6 py-4 transition hover:bg-[#1A1D21] ${
                      index !==
                      data.recent_conversations.length - 1
                        ? 'border-b border-[#C8CBD0]/10'
                        : ''
                    }`}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <p className="truncate text-sm font-medium text-[#F5F5F3] group-hover:text-[#F0C76A]">
                        {conversation.bot_name || 'Untitled Bot'}
                      </p>

                      <span className="shrink-0 text-xs font-semibold text-[#D6A84F]">
                        {conversation.message_count} msgs
                      </span>
                    </div>

                    <div className="mt-2 flex items-center gap-1.5 text-xs text-[#5F656D]">
                      <Clock3 className="h-3.5 w-3.5" />
                      {formatDate(
                        conversation.last_activity ||
                          conversation.created_at
                      )}
                    </div>
                  </Link>
                )
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
