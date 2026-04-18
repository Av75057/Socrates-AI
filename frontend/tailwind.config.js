/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      keyframes: {
        "bounce-dot": {
          "0%, 100%": { transform: "translateY(0)", opacity: "0.45" },
          "50%": { transform: "translateY(-5px)", opacity: "1" },
        },
      },
      animation: {
        "bounce-dot": "bounce-dot 0.6s ease-in-out infinite",
        "bounce-dot-delay-1": "bounce-dot 0.6s ease-in-out 0.15s infinite",
        "bounce-dot-delay-2": "bounce-dot 0.6s ease-in-out 0.3s infinite",
      },
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
