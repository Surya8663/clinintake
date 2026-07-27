/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        /* ── ClinIntake Design System (Light Theme) ──────────────────
         * Shared across all ClinIntake apps.
         * ─────────────────────────────────────────────────────────── */
        'ci-primary':       '#2563eb',
        'ci-primary-hover': '#1d4ed8',
        'ci-primary-light': '#eff6ff',
        'ci-primary-muted': '#dbeafe',
        'ci-surface':       '#f8fafc',
        'ci-surface-alt':   '#eff6ff',
        'ci-border':        '#e2e8f0',
        'ci-border-strong': '#cbd5e1',
      },
      boxShadow: {
        'card':     '0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)',
        'card-lg':  '0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05)',
        'card-hover': '0 10px 15px -3px rgb(0 0 0 / 0.07), 0 4px 6px -4px rgb(0 0 0 / 0.05)',
      },
    },
  },
  plugins: [],
}
