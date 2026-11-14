/** @type {import('tailwindcss').Config} */
const universityGreen = {
  50: "#F1F8F1",
  100: "#DFF0E1",
  200: "#BFE0C3",
  300: "#96CB9B",
  400: "#66AF70",
  500: "#319A43",
  600: "#247C37",
  700: "#1B632D",
  800: "#154E24",
  900: "#103C1D",
  950: "#092B14",
};

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        university: universityGreen,
        "university-blue": {
          50: "#EEF4FB",
          700: "#044694",
          800: "#033876",
        },
        "university-orange": {
          500: "#FF8400",
        },
        // Keep existing neutral utility classes while giving them a green undertone.
        slate: {
          50: "#F5F8F6",
          100: "#EEF2EE",
          200: "#DCE5DC",
          300: "#C4D1C5",
          400: "#87998A",
          500: "#607563",
          600: "#4B5E4D",
          700: "#384A3A",
          800: "#283A2B",
          900: "#1B2C1E",
          950: "#0E1C12",
        },
      },
    },
  },
  plugins: [],
};
