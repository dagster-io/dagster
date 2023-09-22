/** @type {import('tailwindcss').Config} */

const defaultTheme = require('tailwindcss/defaultTheme');

module.exports = {
  content: ['./pages/**/*.{tsx,md}', './components/**/*.{html,md,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Neue Montreal', ...defaultTheme.fontFamily.sans],
        mono: ['Diatype Mono', ...defaultTheme.fontFamily.mono],
      },
      letterSpacing: {},
      borderRadius: {
        xl: '36px',
      },
      boxShadow: {
        inner: 'inset 5px 5px 15px 0 rgba(0, 0, 0, 0.05)',
      },
      colors: {
        'gable-green': '#21463D',
        'gable-green-08': 'rgba(22, 59, 54, 0.08)',
        'gable-green-darker': '#122F2B',
        'sea-foam': '#A7FFBF',
        blurple: '#4F43DD',
        'blurple-darker': '#3F36B1',
        lavender: '#DEDDFF',
        'lavender-darker': '#C9C6FA',
        primary: {
          900: '#09086E',
          700: '#0E0CA7',
          500: '#4F43DD',
          300: '#B9B4F1',
          100: '#EDECFC',
        },
        gray: {
          900: '#231F1B',
          800: '#3A3631',
          700: '#524E48',
          600: '#6B6762',
          500: '#86837F',
          400: '#A19D99',
          300: '#BDBAB7',
          200: '#DAD8D6',
          150: '#F1F1EF',
          100: '#F5F4F2',
          50: '#FAF9F7',
        },
      },
      animation: {
        wiggle: 'wiggle 1s ease-in-out infinite',
      },
      keyframes: {
        wiggle: {
          '0%, 100%': {transform: 'rotate(-3deg)'},
          '50%': {transform: 'rotate(3deg)'},
        },
      },
      height: (theme) => ({
        '(screen-60)': `calc(100vh - ${theme('spacing.60')})`,
      }),
      maxHeight: (theme) => ({
        '(screen-60)': `calc(100vh - ${theme('spacing.60')})`,
      }),
      typography: (theme) => ({
        DEFAULT: {
          css: {
            code: {
              background: theme('colors.gray.100'),
              color: theme('colors.gable-green'),
              overflowWrap: 'break-word',
              fontFamily: theme('fontFamily.mono').join(','),
              fontWeight: theme('fontWeight.medium'),
              fontSize: '14px',
              padding: '4px 6px',
            },
            'code::before': {
              content: '""',
            },
            'code::after': {
              content: '""',
            },
            'a code': {
              background: theme('colors.primary.100'),
              color: theme('colors.blurple'),
              padding: '4px 6px',
              transition: 'all .3s',
            },
            'a code:hover': {
              color: theme('colors.primary.900'),
            },
            'pre a': {
              backgroundColor: theme('colors.primary.100'),
              marginRight: 8,
            },
            strong: {
              fontWeight: theme('fontWeight.medium'),
            },
            em: {
              fontStyle: 'italic',
            },
            h1: {
              color: theme('colors.gable-green'),
              marginTop: 40,
              fontFamily: theme('fontFamily.sans').join(','),
              fontWeight: theme('fontWeight.medium'),
            },
            h2: {
              color: theme('colors.gable-green'),
              fontFamily: theme('fontFamily.sans').join(','),
              fontWeight: theme('fontWeight.medium'),
            },
            h3: {
              color: theme('colors.gable-green'),
              fontFamily: theme('fontFamily.sans').join(','),
              fontWeight: theme('fontWeight.medium'),
            },
            h4: {
              color: theme('colors.gable-green'),
              fontFamily: theme('fontFamily.sans').join(','),
              fontWeight: theme('fontWeight.medium'),
            },
            a: {
              color: theme('colors.blurple'),
              transition: '.3s all',
              textDecoration: 'none',
              fontWeight: theme('fontWeight.normal'),
              overflowWrap: 'break-word',
            },
            'a:hover': {
              textDecoration: 'underline',
            },
            '.scroll-margin-top a': {
              boxShadow: 'none',
            },
            'a strong': {
              color: theme('colors.blurple'),
            },
            'a strong:hover': {
              textDecoration: 'underline',
            },
            p: {
              color: theme('colors.gray.700'),
              fontFamily: theme('fontFamily.sans').join(','),
              fontSize: theme('fontSize.base'),
              lineHeight: '1.4em',
              fontWeight: theme('fontWeight.normal'),
            },
            hr: {
              marginTop: '2em',
              marginBottom: '2em',
            },
          },
        },
      }),
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
