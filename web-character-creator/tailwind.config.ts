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
                background: "var(--background)",
                foreground: "var(--foreground)",
            },
            backgroundImage: {
                'grid-pattern': "linear-gradient(to right, rgba(0, 242, 255, 0.1) 1px, transparent 1px), linear-gradient(to bottom, rgba(0, 242, 255, 0.1) 1px, transparent 1px)",
            },
        },
    },
    plugins: [],
};
export default config;
