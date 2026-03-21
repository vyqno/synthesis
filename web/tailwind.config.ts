import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      colors: {
        background: "#09090B",
        surface: "#111113",
        "surface-2": "#18181B",
        "surface-3": "#27272A",
        border: "rgba(255,255,255,0.07)",
        "border-strong": "rgba(255,255,255,0.12)",
        accent: "#A855F7",
        "accent-2": "#7C3AED",
        green: "#22C55E",
        gold: "#F59E0B",
        red: "#EF4444",
        sky: "#38BDF8",
        muted: "#71717A",
        "muted-2": "#52525B",
        "muted-3": "#3F3F46",
      },
      animation: {
        "border-spin": "border-spin 4s linear infinite",
        "shimmer": "shimmer 2s linear infinite",
        "ticker": "ticker 30s linear infinite",
        "fade-up": "fade-up 0.4s ease forwards",
        "glow-pulse": "glow-pulse 2s ease-in-out infinite",
      },
      keyframes: {
        "border-spin": {
          "100%": { transform: "rotate(360deg)" },
        },
        "shimmer": {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "ticker": {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "glow-pulse": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
