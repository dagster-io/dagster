const defaultTheme = require("tailwindcss/defaultTheme");

module.exports = {
  important: "html",
  purge: [
    "./pages/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
    "./layouts/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      display: ["group-hover"],
      height: (theme) => ({
        "(screen-16)": `calc(100vh - ${theme("spacing.60")})`,
      }),
      maxHeight: (theme) => ({
        "(screen-16)": `calc(100vh - ${theme("spacing.60")})`,
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
          },
        },
      }),
    },
  },
  variants: {
    extend: {},
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography")],
};
