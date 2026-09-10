import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'EmbedIQ Chat',
  description: 'EmbedIQ embedded chat widget',
};

export default function WidgetLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="m-0 min-h-screen overflow-hidden bg-white p-0">
      {children}
    </div>
  );
}