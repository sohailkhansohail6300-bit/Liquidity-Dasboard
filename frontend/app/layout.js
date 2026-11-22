import './globals.css';
import AppProvider from '@/components/AppProvider';

export const metadata = { title: 'Deltablock' };
export const viewport = { width: 'device-width', initialScale: 1, viewportFit: 'cover' };

/* Applies the saved light/dark theme before first paint (same logic and storage key as the prototype's js/theme.js; default is dark). */
const themeScript = "(function(){var r=document.documentElement;r.dataset.theme='dark';try{var s=localStorage.getItem('dbt-theme-v2');if(s==='dark'||s==='light')r.dataset.theme=s;}catch(e){}})();";

export default function RootLayout({ children }) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link href="https://fonts.googleapis.com/css2?family=Exo+2:wght@200&family=IBM+Plex+Mono:wght@500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body suppressHydrationWarning>
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
