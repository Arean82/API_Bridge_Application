/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./bridge_app/templates/**/*.html",
    "./bridge_app/static/js/**/*.js"
  ],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
