import { rem } from "utils/css";

const minWidthCalc = (t, space) => `calc(100% - ${rem(t.space[space])})`;

export const wrapper = {
  zIndex: 9,
  position: "relative",
  p: 3,
  display: "flex",
  alignItems: "center",
  minWidth: t => [minWidthCalc(t, 2), minWidthCalc(t, 3), minWidthCalc(t, 4)],
  bg: "header.bg"
};

export const right = {
  display: "flex",
  alignItems: "center",
  flex: 1
};

export const search = showing => ({
  ml: [showing ? 0 : 3, showing ? 0 : 3, 5],
  mr: [showing ? 0 : 3, showing ? 0 : 3, 5],
  position: "relative",
  width: "100%"
});

const toggleVisiblity = showing => ({
  visibility: [
    showing ? "hidden" : "visible",
    showing ? "hidden" : "visible",
    "visible"
  ],
  width: [showing ? 0 : "auto", showing ? 0 : "auto", "auto"],
  opacity: [showing ? 0 : 1, showing ? 0 : 1, 1],
  transition: "all .3s"
});

export const menuBtn = showing => ({
  ...toggleVisiblity(showing),
  p: 0,
  mr: [showing ? 0 : 2, showing ? 0 : 2, 2],
  display: ["flex", "flex", "none"],
  alignItems: "center",
  outline: "none",
  appearance: "none",
  background: "none",
  border: "none",

  ":hover": {
    cursor: "pointer"
  },

  svg: {
    stroke: "gray.3"
  }
});

export const logo = showing => ({
  ...toggleVisiblity(showing),
  width: [showing ? 0 : 120, showing ? 0 : 120, 120]
});

export const socialIcons = showing => ({
  mr: [2, 2, 4],
  display: [
    showing ? "none" : "inline-grid",
    showing ? "none" : "inline-grid",
    "inline-grid"
  ],

  "a > svg": {
    stroke: "blue.3"
  },
  "a:hover > svg": {
    stroke: "blue.4"
  }
});

export const externalLink = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",

  img: {
    mb: 0
  }
};
