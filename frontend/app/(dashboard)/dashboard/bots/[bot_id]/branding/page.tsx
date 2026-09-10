'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { apiRequest } from '@/lib/api';
import {
  Loader2,
  Save,
  CheckCircle2,
  ChevronLeft,
  Palette,
  Image as ImageIcon,
  MessageSquare,
  AlertCircle,
} from 'lucide-react';

interface BrandSettings {
  bot_id: string;
  company_name: string | null;
  tagline: string | null;
  logo_url: string | null;
  favicon_url: string | null;
  primary_color: string;
  secondary_color: string;
  background_color: string;
  text_color: string;
  accent_color: string;
  font_family: string;
  theme: string;
  border_radius: string;
  widget_position: string;
}

const inputClass =
  'w-full rounded-xl border border-[#C8CBD0]/10 bg-[#0D1013] px-3.5 py-2.5 text-sm text-[#F5F5F3] outline-none transition placeholder:text-[#5F656D] focus:border-[#D6A84F]/50 focus:ring-2 focus:ring-[#D6A84F]/10';

export default function BrandingPage() {
  const params = useParams();
  const botId = params.bot_id as string;

  const [brand, setBrand] = useState<BrandSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<BrandSettings>(`/api/bots/${botId}/branding`)
      .then(setBrand)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : 'Failed to load branding.')
      )
      .finally(() => setLoading(false));
  }, [botId]);

  const update = (field: keyof BrandSettings, value: string) =>
    setBrand((previous) =>
      previous ? { ...previous, [field]: value } : previous
    );

  const handleSave = async () => {
    if (!brand) return;

    setSaving(true);
    setSaved(false);
    setError(null);

    try {
      const updated = await apiRequest<BrandSettings>(
        `/api/bots/${botId}/branding`,
        {
          method: 'PATCH',
          body: JSON.stringify({
            company_name: brand.company_name,
            tagline: brand.tagline,
            logo_url: brand.logo_url,
            primary_color: brand.primary_color,
            secondary_color: brand.secondary_color,
            background_color: brand.background_color,
            text_color: brand.text_color,
            accent_color: brand.accent_color,
            font_family: brand.font_family,
            theme: brand.theme,
            border_radius: brand.border_radius,
            widget_position: brand.widget_position,
          }),
        }
      );

      setBrand(updated);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2500);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to save branding.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#D6A84F]" />
      </div>
    );
  }

  if (!brand) return null;

  const colors = [
    { label: 'Primary', field: 'primary_color' as keyof BrandSettings },
    { label: 'Secondary', field: 'secondary_color' as keyof BrandSettings },
    { label: 'Background', field: 'background_color' as keyof BrandSettings },
    { label: 'Text', field: 'text_color' as keyof BrandSettings },
    { label: 'Accent', field: 'accent_color' as keyof BrandSettings },
  ];

  return (
    <div className="space-y-7">
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <Link
            href={`/dashboard/bots/${botId}`}
            className="mb-4 inline-flex items-center gap-1.5 text-sm text-[#8C9299] transition hover:text-[#F0C76A]"
          >
            <ChevronLeft className="h-4 w-4" />
            Bot overview
          </Link>

          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#D6A84F]">
            Appearance
          </p>

          <h1 className="mt-2 text-2xl font-bold text-[#F5F5F3]">
            Branding & Theme
          </h1>

          <p className="mt-2 text-sm text-[#8C9299]">
            Control how your assistant appears to website visitors.
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#D6A84F] px-4 py-2.5 text-sm font-semibold text-[#080A0D] transition hover:bg-[#F0C76A] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : saved ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <Save className="h-4 w-4" />
          )}

          {saved ? 'Saved' : saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {error && (
        <div className="flex gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-300">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.8fr)]">
        <div className="space-y-6">
          <section className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-6">
            <div className="mb-5 flex items-center gap-3">
              <ImageIcon className="h-5 w-5 text-[#D6A84F]" />
              <div>
                <h2 className="font-semibold text-[#F5F5F3]">
                  Identity
                </h2>
                <p className="text-sm text-[#8C9299]">
                  Name, tagline and logo shown in your widget.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {[
                ['Company Name', 'company_name', 'My Company'],
                ['Tagline', 'tagline', 'How can we help?'],
                ['Logo URL', 'logo_url', 'https://example.com/logo.png'],
              ].map(([label, field, placeholder]) => (
                <label key={field} className="block">
                  <span className="mb-1.5 block text-xs font-medium text-[#C8CBD0]">
                    {label}
                  </span>

                  <input
                    value={(brand[field as keyof BrandSettings] as string) || ''}
                    onChange={(e) =>
                      update(field as keyof BrandSettings, e.target.value)
                    }
                    placeholder={placeholder}
                    className={inputClass}
                  />
                </label>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-6">
            <div className="mb-5 flex items-center gap-3">
              <Palette className="h-5 w-5 text-[#D6A84F]" />
              <div>
                <h2 className="font-semibold text-[#F5F5F3]">
                  Colors
                </h2>
                <p className="text-sm text-[#8C9299]">
                  Fine-tune the automatically extracted website palette.
                </p>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {colors.map(({ label, field }) => (
                <div
                  key={field}
                  className="flex items-center gap-3 rounded-xl border border-[#C8CBD0]/10 bg-[#0D1013] p-3"
                >
                  <input
                    type="color"
                    value={(brand[field] as string) || '#000000'}
                    onChange={(e) => update(field, e.target.value)}
                    className="h-10 w-10 cursor-pointer rounded-lg border-0 bg-transparent"
                  />

                  <div className="min-w-0">
                    <p className="text-xs font-medium text-[#C8CBD0]">
                      {label}
                    </p>
                    <p className="mt-0.5 font-mono text-xs text-[#8C9299]">
                      {brand[field] as string}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-6">
            <div className="mb-5 flex items-center gap-3">
              <MessageSquare className="h-5 w-5 text-[#D6A84F]" />
              <h2 className="font-semibold text-[#F5F5F3]">
                Widget
              </h2>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <label>
                <span className="mb-1.5 block text-xs font-medium text-[#C8CBD0]">
                  Position
                </span>
                <select
                  value={brand.widget_position}
                  onChange={(e) => update('widget_position', e.target.value)}
                  className={inputClass}
                >
                  <option value="bottom-right">Bottom Right</option>
                  <option value="bottom-left">Bottom Left</option>
                </select>
              </label>

              <label>
                <span className="mb-1.5 block text-xs font-medium text-[#C8CBD0]">
                  Theme
                </span>
                <select
                  value={brand.theme}
                  onChange={(e) => update('theme', e.target.value)}
                  className={inputClass}
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                </select>
              </label>
            </div>
          </section>
        </div>

        <section className="h-fit rounded-2xl border border-[#C8CBD0]/10 bg-[#111418] p-6 xl:sticky xl:top-6">
          <div className="mb-5">
            <h2 className="font-semibold text-[#F5F5F3]">
              Live Preview
            </h2>
            <p className="mt-1 text-sm text-[#8C9299]">
              Approximation of your visitor-facing widget.
            </p>
          </div>

          <div className="rounded-2xl border border-[#C8CBD0]/10 bg-[#080A0D] p-4">
            <div
              className="overflow-hidden shadow-2xl"
              style={{
                backgroundColor: brand.background_color,
                color: brand.text_color,
                fontFamily: brand.font_family,
                borderRadius: brand.border_radius,
              }}
            >
              <div
                className="flex items-center gap-3 p-4"
                style={{ backgroundColor: brand.primary_color }}
              >
                {brand.logo_url ? (
                  <img
                    src={brand.logo_url}
                    alt=""
                    className="h-8 max-w-[110px] object-contain"
                  />
                ) : null}

                <div className="min-w-0">
                  <p className="truncate text-sm font-bold text-white">
                    {brand.company_name || 'Your Company'}
                  </p>
                  <p className="truncate text-xs text-white/75">
                    {brand.tagline || 'AI Assistant'}
                  </p>
                </div>
              </div>

              <div className="min-h-[260px] space-y-4 p-4">
                <div className="flex justify-start">
                  <div className="max-w-[85%] rounded-xl bg-black/5 px-3 py-2 text-sm">
                    Hi! How can I help you today?
                  </div>
                </div>

                <div className="flex justify-end">
                  <div
                    className="max-w-[85%] rounded-xl px-3 py-2 text-sm text-white"
                    style={{ backgroundColor: brand.primary_color }}
                  >
                    What services do you provide?
                  </div>
                </div>

                <div className="flex justify-start">
                  <div className="max-w-[85%] rounded-xl bg-black/5 px-3 py-2 text-sm">
                    I can answer questions using this website&apos;s knowledge base.
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 flex justify-end">
            <div
              className="flex h-14 w-14 items-center justify-center rounded-full shadow-xl"
              style={{ backgroundColor: brand.primary_color }}
            >
              <MessageSquare className="h-6 w-6 text-white" />
            </div>
          </div>

          <p className="mt-2 text-right text-xs text-[#5F656D]">
            Launcher preview
          </p>
        </section>
      </div>
    </div>
  );
}
