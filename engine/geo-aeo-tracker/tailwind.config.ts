import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        th: {
          bg: 'var(--bg)',
          'bg-elevated': 'var(--bg-elevated)',
          'bg-subtle': 'var(--bg-subtle)',
          'bg-hover': 'var(--bg-hover)',
          fg: 'var(--fg)',
          'fg-muted': 'var(--fg-muted)',
          'fg-subtle': 'var(--fg-subtle)',
          border: 'var(--border)',
          'border-subtle': 'var(--border-subtle)',
          'border-strong': 'var(--border-strong)',
          accent: 'var(--accent)',
          'accent-hover': 'var(--accent-hover)',
          'accent-soft': 'var(--accent-soft)',
          'accent-muted': 'var(--accent-muted)',
          success: 'var(--success)',
          'success-soft': 'var(--success-soft)',
          warning: 'var(--warning)',
          'warning-soft': 'var(--warning-soft)',
          danger: 'var(--danger)',
          'danger-soft': 'var(--danger-soft)',
          chatgpt: 'var(--chatgpt)',
          perplexity: 'var(--perplexity)',
          copilot: 'var(--copilot)',
          gemini: 'var(--gemini)',
          'google-ai': 'var(--google-ai)',
        },
        text: {
          th: 'var(--fg)',
          'th-muted': 'var(--fg-muted)',
          'th-subtle': 'var(--fg-subtle)',
          'th-inverse': 'var(--bg)',
          'th-accent': 'var(--accent)',
          'th-success': 'var(--success)',
          'th-warning': 'var(--warning)',
          'th-danger': 'var(--danger)',
        },
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-jetbrains-mono)', 'monospace'],
      },
      spacing: {
        1: 'var(--space-1)',
        2: 'var(--space-2)',
        3: 'var(--space-3)',
        4: 'var(--space-4)',
        5: 'var(--space-5)',
        6: 'var(--space-6)',
        8: 'var(--space-8)',
        10: 'var(--space-10)',
        12: 'var(--space-12)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        DEFAULT: 'var(--radius)',
        lg: 'var(--radius-lg)',
        full: 'var(--radius-full)',
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        DEFAULT: 'var(--shadow)',
        md: 'var(--shadow-md)',
        lg: 'var(--shadow-lg)',
      },
      transitionDuration: {
        fast: 'var(--transition-fast)',
        DEFAULT: 'var(--transition)',
        slow: 'var(--transition-slow)',
      },
    },
  },
  plugins: [],
}

export default config