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
        obsidian: {
          950: "#090a0d",
          900: "#0e1117",
          850: "#131720",
          800: "#181d28",
          700: "#222938",
        },
        tactical: {
          border: "#252d3d",
          amber: "#f59e0b",
          orange: "#ea580c",
          lime: "#84cc16",
          cyan: "#06b6d4",
          red: "#ef4444",
        },
        newsprint: {
          100: "#fbfaf8",
          200: "#f4f1ea",
          800: "#2a2723",
          900: "#1a1816",
        }
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      boxShadow: {
        tactile: "3px 3px 0 #181d28",
        "tactile-dark": "3px 3px 0 #090a0d",
      }
    },
  },
  plugins: [],
};
export default config;
