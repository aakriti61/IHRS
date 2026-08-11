/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0E2233",
        teal: { DEFAULT: "#1B6FA8", dark: "#124D79", light: "#DCEEF7" },
        navy: { DEFAULT: "#16324F", dark: "#0E2038" },
        gold: { DEFAULT: "#C98A2C", light: "#F5E4C3" },
        surface: "#F5F7F9",
        danger: "#B3432D",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Inter", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(14,42,43,0.06), 0 8px 24px rgba(14,42,43,0.06)",
      },
    },
  },
  plugins: [],
};
