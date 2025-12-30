/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Musical notation inspired colors
        staff: {
          50: "#fef7f0",
          100: "#fdecd9",
          200: "#fad4b1",
          300: "#f6b67f",
          400: "#f08d4a",
          500: "#ec6e25",
          600: "#dd541b",
          700: "#b73f18",
          800: "#93331b",
          900: "#772d19",
        },
        ink: {
          50: "#f6f6f7",
          100: "#e2e3e5",
          200: "#c5c7cb",
          300: "#a0a3aa",
          400: "#7b7f88",
          500: "#60646d",
          600: "#4c4f57",
          700: "#3e4147",
          800: "#35373c",
          900: "#1a1b1e",
          950: "#0d0e0f",
        },
      },
      fontFamily: {
        display: ['"Playfair Display"', "Georgia", "serif"],
        mono: ['"JetBrains Mono"', '"Fira Code"', "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.5s ease-out",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

