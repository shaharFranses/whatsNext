/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: '#0a0a0c',
                card: '#16161a',
                primary: '#3b82f6',
                accent: '#8b5cf6',
            },
        },
    },
    plugins: [],
}
