import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: "#132038", 2: "#1c2d4d" },
        paper: { DEFAULT: "#F1E9D8", 2: "#E7DBC0", 3: "#DDCFAE" },
        brass: "#B9862F",
        burgundy: "#7C2436",
        line: "#C9BB98",
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "Georgia", "serif"],
        body: ["var(--font-work-sans)", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
