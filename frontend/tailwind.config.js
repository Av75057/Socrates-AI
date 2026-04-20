/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      keyframes: {
        "bounce-dot": {
          "0%, 100%": { transform: "translateY(0)", opacity: "0.45" },
          "50%": { transform: "translateY(-5px)", opacity: "1" },
        },
        toastIn: {
          from: { opacity: "0", transform: "translateY(-8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        wisdomPulse: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(234, 179, 8, 0.35)" },
          "50%": { boxShadow: "0 0 0 10px rgba(234, 179, 8, 0)" },
        },
      },
      animation: {
        "bounce-dot": "bounce-dot 0.6s ease-in-out infinite",
        "bounce-dot-delay-1": "bounce-dot 0.6s ease-in-out 0.15s infinite",
        "bounce-dot-delay-2": "bounce-dot 0.6s ease-in-out 0.3s infinite",
        toastIn: "toastIn 0.35s ease-out both",
        wisdomPulse: "wisdomPulse 0.9s ease-out 1",
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
