const defaultTheme = require("tailwindcss/defaultTheme");
const colors = require("tailwindcss/colors");

module.exports = {
  important: "html",
  purge: [
    "./pages/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
    "./layouts/**/*.{js,jsx,ts,tsx}",
    "../content-crag/**/*.mdx",
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
      colors: {
        gray: colors.trueGray,
        cyan: colors.cyan,
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
            "pre a": {
              backgroundColor: theme("colors.yellow.100"),
              marginRight: 8,
            },
          },
        },
        dark: {
          css: [
            {
              color: theme("colors.gray.300"),
              '[class~="lead"]': {
                color: theme("colors.gray.300"),
              },
              a: {
                color: theme("colors.white"),
              },
              strong: {
                color: theme("colors.white"),
              },
              "ol > li::before": {
                color: theme("colors.gray.400"),
              },
              "ul > li::before": {
                backgroundColor: theme("colors.gray.600"),
              },
              hr: {
                borderColor: theme("colors.gray.200"),
              },
              blockquote: {
                color: theme("colors.gray.200"),
                borderLeftColor: theme("colors.gray.600"),
              },
              h1: {
                color: theme("colors.white"),
              },
              h2: {
                color: theme("colors.white"),
              },
              h3: {
                color: theme("colors.white"),
              },
              h4: {
                color: theme("colors.white"),
              },
              "figure figcaption": {
                color: theme("colors.gray.400"),
              },
              code: {
                color: theme("colors.white"),
              },
              "a code": {
                color: theme("colors.white"),
              },
              pre: {
                color: theme("colors.gray.200"),
                backgroundColor: theme("colors.gray.800"),
              },
              thead: {
                color: theme("colors.white"),
                borderBottomColor: theme("colors.gray.400"),
              },
              "tbody tr": {
                borderBottomColor: theme("colors.gray.600"),
              },
            },
          ],
        },
      }),
    },
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography")],
};
