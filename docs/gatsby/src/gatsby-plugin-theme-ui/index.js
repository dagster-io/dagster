import { rem } from "utils/css";
import colors, { newColors } from "./colors";

export default {
  breakpoints: ["600px", "1024px", "1366px"],
  colors: {
    ...colors,
    primary: colors.blue[2],
    secondary: colors.indigo[2],
    text: colors.dark[0],
    bodyBg: colors.white,
    border: colors.lightGray[3],
    header: {
      bg: colors.white
    },
    sidebar: {
      bg: newColors.white,
      color: newColors.gray
    }
  },
  fonts: {
    body: 'Inter, "Source Sans Pro", system-ui, sans-serif',
    heading: 'Inter, "Work Sans", system-ui, sans-serif',
    mono:
      '"Fira Code", "SFMono-Regular", "Consolas", "Roboto Mono", "Droid Sand Mono", "Liberation Mono", "Menlo", "Courier", monospace'
  },
  radii: {
    square: 0,
    radius: 6,
    rounded: 10,
    circle: 9999
  },
  shadows: [
    "none",
    "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);",
    "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);",
    "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);",
    "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);",
    "0 25px 50px -12px rgba(0, 0, 0, 0.25);"
  ],
  styles: {
    root: {
      lineHeight: 1.55,
      minHeight: "100vh",
      fontFamily: "body",
      fontSize: 3,
      color: "text",
      bg: "bodyBg"
    },
    pre: {
      p: 0
    },
    code: {
      p: 1,
      mx: 1,
      fontFamily: "mono",
      color: "red.0",
      border: t => `1px solid ${t.colors.lightGray[1]}`
    }
  },
  header: {
    gutter: [rem(88), rem(100), rem(155)]
  }
};
