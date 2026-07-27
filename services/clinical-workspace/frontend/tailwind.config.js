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
         * Shared across Clinical Workspace, Drug Interaction, and
         * Patient Identity apps.  These tokens are the single source
         * of truth — phases 3 & 4 should import the same palette.
         *
         * Surface / Background
         *   page-bg       → white (#ffffff)
         *   surface       → slate-50 (#f8fafc)
         *   surface-alt   → blue-50 (#eff6ff)
         *
         * Primary Accent
         *   primary       → blue-600 (#2563eb)
         *   primary-hover → blue-700 (#1d4ed8)
         *   primary-light → blue-50 (#eff6ff)
         *   primary-muted → blue-100 (#dbeafe)
         *
         * Borders
         *   border        → slate-200 (#e2e8f0)
         *   border-strong → slate-300 (#cbd5e1)
         *
         * Text
         *   text-primary   → slate-800 (#1e293b)
         *   text-secondary → slate-500 (#64748b)
         *   text-muted     → slate-400 (#94a3b8)
         *
         * Status — Success (approved)
         *   success-bg     → emerald-50 (#ecfdf5)
         *   success-border → emerald-200 (#a7f3d0)
         *   success-text   → emerald-700 (#047857)
         *
         * Status — Error (rejected / failure)
         *   error-bg       → rose-50 (#fff1f2)
         *   error-border   → rose-200 (#fecdd3)
         *   error-text     → rose-700 (#be123c)
         *
         * Status — Warning
         *   warning-bg     → amber-50 (#fffbeb)
         *   warning-border → amber-200 (#fde68a)
         *   warning-text   → amber-700 (#b45309)
         *
         * Status — Info / Saved
         *   info-bg        → blue-50 (#eff6ff)
         *   info-border    → blue-200 (#bfdbfe)
         *   info-text      → blue-700 (#1d4ed8)
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
