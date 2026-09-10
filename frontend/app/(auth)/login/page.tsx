'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Sparkles, Loader2, AlertCircle } from 'lucide-react';
import { setToken } from '@/lib/auth';
import { apiRequest } from '@/lib/api';

interface LoginResponse {
  access_token: string;
  token_type: string;
}

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await apiRequest<LoginResponse>('/api/auth/login', {
        method: 'POST',
        noAuth: true,
        body: JSON.stringify({ email, password }),
      });

      setToken(data.access_token);
      router.push('/dashboard');
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : 'Login failed. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-md">
      <Link
        href="/"
        className="mb-8 flex items-center justify-center gap-3"
      >
        <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-[#D6A84F]/30 bg-[#D6A84F]/10 text-[#F0C76A]">
          <Sparkles className="h-5 w-5" />
        </div>

        <span className="text-2xl font-bold tracking-tight text-[#F5F5F3]">
          Embed<span className="text-[#D6A84F]">IQ</span>
        </span>
      </Link>

      <div className="rounded-2xl border border-[#2A2E34] bg-[#111418] p-8 shadow-2xl">
        <div className="mb-7">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
            Welcome back
          </p>

          <h1 className="text-2xl font-bold text-[#F5F5F3]">
            Sign in to EmbedIQ
          </h1>

          <p className="mt-2 text-sm text-[#8C9299]">
            Access your bots, knowledge bases and analytics.
          </p>
        </div>

        {error && (
          <div className="mb-5 flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="email"
              className="mb-2 block text-sm font-medium text-[#C8CBD0]"
            >
              Email address
            </label>

            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="w-full rounded-xl border border-[#34383E] bg-[#1A1D21] px-4 py-3 text-sm text-[#F5F5F3] outline-none transition placeholder:text-[#6F757D] focus:border-[#D6A84F] focus:ring-2 focus:ring-[#D6A84F]/15"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-sm font-medium text-[#C8CBD0]"
            >
              Password
            </label>

            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-xl border border-[#34383E] bg-[#1A1D21] px-4 py-3 text-sm text-[#F5F5F3] outline-none transition placeholder:text-[#6F757D] focus:border-[#D6A84F] focus:ring-2 focus:ring-[#D6A84F]/15"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#D6A84F] px-4 py-3 text-sm font-semibold text-[#080A0D] transition hover:bg-[#F0C76A] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Signing in…</span>
              </>
            ) : (
              <span>Sign in</span>
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-[#8C9299]">
          Don&apos;t have an account?{' '}
          <Link
            href="/register"
            className="font-semibold text-[#D6A84F] transition hover:text-[#F0C76A]"
          >
            Create one free
          </Link>
        </p>
      </div>
    </div>
  );
}
