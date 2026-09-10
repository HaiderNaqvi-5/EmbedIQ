'use client';

import { useEffect, useState } from 'react';
import {
  Settings,
  UserRound,
  Mail,
  ShieldCheck,
  Loader2,
  AlertCircle,
  KeyRound,
  Database,
  LockKeyhole,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';

interface CurrentUser {
  id?: string;
  user_id?: string;
  email?: string;
  is_active?: boolean;
  created_at?: string;
}

function displayId(user: CurrentUser) {
  return user.id || user.user_id || 'Unavailable';
}

export default function SettingsPage() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<CurrentUser>('/api/auth/me')
      .then((response) => {
        setUser(response);
        setError(null);
      })
      .catch((err: unknown) =>
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load account information.'
        )
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
          Settings
        </p>

        <h1 className="text-3xl font-bold tracking-tight text-[#F5F5F3]">
          Account Settings
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-[#9EA3AA]">
          View your EmbedIQ account and current platform
          configuration.
        </p>
      </div>

      {loading && (
        <div className="flex min-h-[320px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-[#D6A84F]" />
        </div>
      )}

      {!loading && error && (
        <div className="flex items-start gap-3 rounded-2xl border border-red-500/20 bg-red-500/5 px-5 py-4 text-sm text-red-300">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />

          <div>
            <p className="font-semibold">
              Unable to load account
            </p>

            <p className="mt-1 text-red-300/70">
              {error}
            </p>
          </div>
        </div>
      )}

      {!loading && !error && user && (
        <>
          <section className="overflow-hidden rounded-2xl border border-[#C8CBD0]/10 bg-[#111418]">
            <div className="border-b border-[#C8CBD0]/10 p-6">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-[#D6A84F]/20 bg-[#D6A84F]/10">
                  <UserRound className="h-6 w-6 text-[#D6A84F]" />
                </div>

                <div>
                  <h2 className="font-semibold text-[#F5F5F3]">
                    Account
                  </h2>

                  <p className="mt-1 text-sm text-[#8C9299]">
                    Information associated with your authenticated
                    EmbedIQ account.
                  </p>
                </div>
              </div>
            </div>

            <div className="divide-y divide-[#C8CBD0]/10">
              <div className="flex flex-col gap-2 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <Mail className="h-4 w-4 text-[#D6A84F]" />

                  <div>
                    <p className="text-sm font-medium text-[#C8CBD0]">
                      Email address
                    </p>

                    <p className="mt-1 text-xs text-[#5F656D]">
                      Used to authenticate your account.
                    </p>
                  </div>
                </div>

                <p className="break-all text-sm text-[#F5F5F3]">
                  {user.email || 'Unavailable'}
                </p>
              </div>

              <div className="flex flex-col gap-2 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <KeyRound className="h-4 w-4 text-[#D6A84F]" />

                  <div>
                    <p className="text-sm font-medium text-[#C8CBD0]">
                      Account ID
                    </p>

                    <p className="mt-1 text-xs text-[#5F656D]">
                      Internal identifier for this workspace account.
                    </p>
                  </div>
                </div>

                <code className="max-w-full break-all rounded-lg border border-[#C8CBD0]/10 bg-[#080A0D] px-3 py-2 text-xs text-[#9EA3AA]">
                  {displayId(user)}
                </code>
              </div>

              <div className="flex flex-col gap-2 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <ShieldCheck className="h-4 w-4 text-[#D6A84F]" />

                  <div>
                    <p className="text-sm font-medium text-[#C8CBD0]">
                      Account status
                    </p>

                    <p className="mt-1 text-xs text-[#5F656D]">
                      Current authentication status.
                    </p>
                  </div>
                </div>

                <span
                  className={`inline-flex w-fit rounded-full border px-2.5 py-1 text-xs font-semibold ${
                    user.is_active === false
                      ? 'border-red-500/20 bg-red-500/10 text-red-300'
                      : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300'
                  }`}
                >
                  {user.is_active === false
                    ? 'Inactive'
                    : 'Active'}
                </span>
              </div>
            </div>
          </section>

          <div className="grid gap-5 md:grid-cols-3">
            <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5">
              <Database className="h-5 w-5 text-[#D6A84F]" />

              <h3 className="mt-4 font-semibold text-[#F5F5F3]">
                Bot Isolation
              </h3>

              <p className="mt-2 text-sm leading-6 text-[#8C9299]">
                Website knowledge and conversations remain scoped
                to their individual chatbot.
              </p>
            </div>

            <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5">
              <LockKeyhole className="h-5 w-5 text-[#D6A84F]" />

              <h3 className="mt-4 font-semibold text-[#F5F5F3]">
                Authentication
              </h3>

              <p className="mt-2 text-sm leading-6 text-[#8C9299]">
                Dashboard APIs require your authenticated EmbedIQ
                session.
              </p>
            </div>

            <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-5">
              <Settings className="h-5 w-5 text-[#D6A84F]" />

              <h3 className="mt-4 font-semibold text-[#F5F5F3]">
                Preferences
              </h3>

              <p className="mt-2 text-sm leading-6 text-[#8C9299]">
                Editable account preferences will appear here when
                supported by the backend.
              </p>
            </div>
          </div>

          <section className="rounded-2xl border border-[#D6A84F]/15 bg-[#D6A84F]/5 p-5">
            <div className="flex gap-3">
              <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-[#D6A84F]" />

              <div>
                <p className="text-sm font-semibold text-[#E8EAEC]">
                  Read-only settings
                </p>

                <p className="mt-1 text-sm leading-6 text-[#8C9299]">
                  EmbedIQ currently exposes account information but
                  does not provide backend endpoints for editing the
                  profile, changing passwords or managing application
                  preferences. Those controls are intentionally not
                  presented as functional buttons.
                </p>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
