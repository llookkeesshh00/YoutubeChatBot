import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#151515",
        paper: "#f7f4ef",
        line: "#ded8ce",
        accent: "#2563eb",
        mint: "#2f9e7e"
      }
    }
  },
  plugins: []
};

export default config;

