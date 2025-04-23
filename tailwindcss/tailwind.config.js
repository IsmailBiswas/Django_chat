/** @type {import('tailwindcss').Config } */
export default {
    mode: 'jit',
    content: ["../**/templates/**/*.html"],
    theme: {
        extend: {
            colors: {
                'dark-bg': '#121212',
            }
        },
    },
    plugins: [],
}
