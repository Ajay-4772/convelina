import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#faf9f6",
        surface: "#ffffff",
        "surface-muted": "#f5f3ef",
        "surface-card": "#ffffff",
        border: "#e5e2dc",
        "border-subtle": "#eeeae3",
        charcoal: {
          900: "#18181b",
          800: "#27272a",
          700: "#3f3f46",
          600: "#52525b",
          500: "#71717a",
          400: "#a1a1aa",
          300: "#d4d4d8",
          200: "#e4e4e7",
          100: "#f4f4f5",
          50: "#fafafa",
        },
        sand: {
          50: "#fdfcfa",
          100: "#f8f6f0",
          200: "#f1eee4",
          300: "#e6e1d3",
          400: "#d6cfbe",
        },
        accent: {
          DEFAULT: "#18181b",
          hover: "#27272a",
        }
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        serif: [
          "Newsreader",
          "Charter",
          "Georgia",
          "Cambria",
          "Times New Roman",
          "serif",
        ],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)",
        elevated: "0 4px 12px -2px rgba(0, 0, 0, 0.05), 0 2px 6px -2px rgba(0, 0, 0, 0.03)",
        floating: "0 20px 25px -5px rgba(0, 0, 0, 0.06), 0 8px 10px -6px rgba(0, 0, 0, 0.04)",
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.037), inset 0 0 0 1px rgba(255, 255, 255, 0.6)",
        "glass-hover": "0 14px 40px 0 rgba(0, 0, 0, 0.06), inset 0 0 0 1px rgba(255, 255, 255, 0.9)",
        "glass-inner": "inset 0 1px 1px 0 rgba(255, 255, 255, 0.8), inset 0 -1px 2px 0 rgba(0, 0, 0, 0.03)",
      },
      animation: {
        "float-slow": "float 8s ease-in-out infinite",
        "pulse-subtle": "pulseGlow 4s ease-in-out infinite",
        "shimmer": "shimmer 2.5s infinite linear",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "0.4", transform: "scale(1)" },
          "50%": { opacity: "0.75", transform: "scale(1.05)" },
        },
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
