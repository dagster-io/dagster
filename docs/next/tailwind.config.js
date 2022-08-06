const defaultTheme = require("tailwindcss/defaultTheme");

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
        mono: ["Diatype Mono", ...defaultTheme.fontFamily.mono],
      },
      borderRadius: {
        xl: "36px",
      },
      boxShadow: {
        inner: "inset 5px 5px 15px 0 rgba(0, 0, 0, 0.05)",
      },
      colors: {
        "gable-green": "#21463D",
        "gable-green-08": "rgba(22, 59, 54, 0.08)",
        "gable-green-darker": "#122F2B",
        "sea-foam": "#A7FFBF",
        blurple: "#4F43DD",
        "blurple-darker": "#3F36B1",
        lavender: "#DEDDFF",
        "lavender-darker": "#C9C6FA",
        primary: {
          900: "#09086E",
          700: "#0E0CA7",
          500: "#4F43DD",
          300: "#B9B4F1",
          100: "#EDECFC",
        },
        gray: {
          900: "#231F1B",
          800: "#3A3631",
          700: "#524E48",
          600: "#6B6762",
          500: "#86837F",
          400: "#A19D99",
          300: "#BDBAB7",
          200: "#DAD8D6",
          150: "#F1F1EF",
          100: "#F5F4F2",
          50: "#FAF9F7",
        },
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
              overflowWrap: "break-word",
            },
            "code::before": {
              content: '""',
            },
            "code::after": {
              content: '""',
            },
            "a code": {
              background: theme("colors.gray.100"),
              color: theme("colors.primary.900"),
              padding: "4px 6px",
              transition: "all .3s",
            },
            "a code:hover": {
              text_decoration: "underline",
              background: theme("colors.primary.100"),
              color: theme("colors.blurple"),
            },
            "pre a": {
              backgroundColor: theme("colors.primary.100"),
              marginRight: 8,
            },
            a: {
              color: theme("colors.primary.900"),
              transition: ".3s all",
              textDecoration: "none",
              overflowWrap: "break-word",
            },
            "a:hover": {
              textDecoration: "underline",
            },
            ".scroll-margin-top a": {
              boxShadow: "none",
            },
            "a strong": {
              color: theme("colors.primary.900"),
            },
            "a strong:hover": {
              textDecoration: "underline",
            },
          },
        },
      }),
    },
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography")],
};
