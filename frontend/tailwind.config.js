/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        university: {
          700: "#123c35",
          800: "#0d302a",
        },
      },
    },
  },
  plugins: [],
};
