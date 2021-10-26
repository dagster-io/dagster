const defaultTheme = require("tailwindcss/defaultTheme");
const colors = require("tailwindcss/colors");
const { red } = require("tailwindcss/colors");

module.exports = {
  important: "html",
  purge: [
    "./pages/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
    "./layouts/**/*.{js,jsx,ts,tsx}",
    "../content/**/*.mdx",
  ],
  darkMode: "class",
  variants: {
    extend: {
      display: ["group-hover"],
      scale: ["group-hover"],
      rotate: ["group-hover"],
      animation: ["hover"],
      typography: ["dark"],
    },
  },
  theme: {
    extend: {
      fontFamily: {
        sans: ["Neue Montreal", ...defaultTheme.fontFamily.sans],
        mono: ["Diatype Mono", ...defaultTheme.fontFamily.mono]
      },
      borderRadius: {
        'xl': '36px'
      },
      boxShadow: {
        inner: 'inset 5px 5px 15px 0 rgba(0, 0, 0, 0.05)',
      },
      colors: {
        gray: colors.trueGray, //remove later
        cyan: colors.cyan, //remove later
        "gable-green": "#163B36",
        "sea-foam": "#A7FFBF",
        "blurple": "#4F43DD",
        "lavender": "#DEDDFF",
        primary: {
          "900":"#0E0CA7",
          "500":"#4F43DD",
          "300":"#B9B4F1",
          "100": "#EDECFC"
        },
        gray: {
          "900": '#231F1B',
          "800": '#3A3631',
          "700": '#524E48',
          "600": '#6B6762',
          "500": '#86837F',
          "400": '#A19D99',
          "300": '#BDBAB7',
          "200": '#DAD8D6',
          "100": '#F5F4F2',
          "50": '#FEFDFB'
        }
      },
      animation: {
        wiggle: "wiggle 1s ease-in-out infinite",
      },
      keyframes: {
        wiggle: {
          "0%, 100%": { transform: "rotate(-3deg)" },
          "50%": { transform: "rotate(3deg)" },
        },
      },
      height: (theme) => ({
        "(screen-60)": `calc(100vh - ${theme("spacing.60")})`,
      }),
      maxHeight: (theme) => ({
        "(screen-60)": `calc(100vh - ${theme("spacing.60")})`,
      }),
      typography: (theme) => ({
        DEFAULT: {
          css: {
            code: {
              background_color: theme(
                "colors.gray.900",
                defaultTheme.colors.gray[900]
              ),
            },
            "code::before": {
              content: '""',
            },
            "code::after": {
              content: '""',
            },
            "a code": {
              background: theme("colors.gray.100"),
              color: theme("colors.blurple"),
              padding: "4px 6px",
              transition: "all .3s",
            },
            "a code:hover": {
              text_decoration: "underline",
              background: theme("colors.primary.100"),
              color: theme("colors.primary.900"),
            },
            "pre a": {
              backgroundColor: theme("colors.yellow.100"),
              marginRight: 8,
            },
          },
        }
      }),
    },
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography")],
};
