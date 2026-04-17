/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        socrates: {
          bg: "#0f172a",
          user: "#2563eb",
          ai: "#1e293b",
        },
      },
    },
  },
  plugins: [],
};
