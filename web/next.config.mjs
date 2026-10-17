const API = (process.env.NEXT_PUBLIC_API_URL || "https://gigsaathi-silk.vercel.app").replace(/\/$/, "");
const dev = process.env.NODE_ENV !== "production";

// tesseract.js (on-device OCR) loads its worker, wasm core and language data from jsDelivr.
const OCR_CDN = "https://cdn.jsdelivr.net";
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' blob: ${OCR_CDN}${dev ? " 'unsafe-eval'" : ""}`,
  `worker-src 'self' blob: ${OCR_CDN}`,
  `connect-src 'self' ${API} ${OCR_CDN} https://tessdata.projectnaptha.com${dev ? " ws:" : ""}`,
  "img-src 'self' data: blob:",
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self' data:",
  "media-src 'self' blob:",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  // mic + location are only requested after the in-app consent prompt; camera is never used
  { key: "Permissions-Policy", value: "camera=(), microphone=(self), geolocation=(self), payment=(), usb=()" },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
];

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  eslint: { ignoreDuringBuilds: true },
  // tree-shake icon and chart libraries so each page only ships what it uses
  experimental: { optimizePackageImports: ["lucide-react", "recharts"] },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};
export default nextConfig;
