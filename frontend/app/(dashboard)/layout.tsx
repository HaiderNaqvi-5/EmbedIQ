'use client';

/**
 * Dashboard group layout.
 * Renders: sidebar navigation + AuthGuard (redirects to /login if no JWT).
 * The AuthGuard runs client-side because localStorage is unavailable server-side.
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { Bot, LayoutDashboard, LogOut, Loader2, Sparkles, Database, BarChart3, Settings } from 'lucide-react';
import { getToken, clearToken } from '@/lib/auth';
import { apiRequest } from '@/lib/api';

interface Me {
  email: string;
  id: string;
}

const NAV_ITEMS = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, exact: true },
  { label: 'My Bots', href: '/dashboard/bots', icon: Bot },
  { label: 'Knowledge', href: '/dashboard/knowledge', icon: Database },
  { label: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  { label: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<Me | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace('/login');
      return;
    }

    // Fetch current user info for the sidebar
    apiRequest<Me>('/api/auth/me')
      .then((u) => {
        setUser(u);
        setAuthChecked(true);
      })
      .catch(() => {
        clearToken();
        router.replace('/login');
      });
  }, [router]);

  function handleLogout() {
    clearToken();
    router.push('/login');
  }

  // Show full-screen spinner while verifying auth
  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#080A0D]">
        <Loader2 className="h-8 w-8 animate-spin text-[#D6A84F]" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#080A0D]">
      {/* ─── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className="w-64 shrink-0 flex flex-col bg-[#0D1014] border-r border-[#C8CBD0]/10 shadow-2xl">
        {/* Logo */}
        <div className="h-20 flex items-center px-5 border-b border-[#C8CBD0]/10">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-[#D6A84F]/15 border border-[#D6A84F]/30 flex items-center justify-center text-[#F0C76A] shadow-lg">
              <Sparkles className="w-4 h-4" />
            </div>
            <span className="text-xl font-bold tracking-tight text-[#F5F5F3]">
              Embed<span className="text-[#D6A84F]">IQ</span>
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const { label, href, icon: Icon } = item;

            const active =
              'exact' in item && item.exact
                ? pathname === item.href
                : pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={href + label}
                href={href}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? 'bg-[#D6A84F]/12 text-[#F0C76A] border border-[#D6A84F]/20'
                    : 'text-[#9EA3AA] hover:bg-[#1A1D21] hover:text-[#F5F5F3] border border-transparent'
                }`}
              >
                <Icon className={`h-4 w-4 shrink-0 ${active ? 'text-[#D6A84F]' : ''}`} />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User footer */}
        <div className="border-t border-[#C8CBD0]/10 p-4">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-[#D6A84F]/20 text-[#F0C76A] border border-[#D6A84F]/20 flex items-center justify-center text-xs font-bold uppercase shrink-0">
              {user?.email?.[0] ?? '?'}
            </div>
            <span className="text-xs text-[#9EA3AA] truncate" title={user?.email}>
              {user?.email}
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-2 rounded-lg px-3 py-2 text-sm text-[#8C9299] hover:bg-[#1A1D21] hover:text-[#F5F5F3] transition-colors"
          >
            <LogOut className="h-4 w-4 shrink-0" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* ─── Main content ─────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
