import { rem } from "utils/css";

export const search = showing => ({
  ml: [showing ? 0 : 3, 3, 4],
  overflow: ["hidden", "auto"],
  display: "flex",
  alignItems: "center",
  fontSize: 4,

  ":hover": {
    cursor: "pointer"
  },

  svg: {
    mr: 3,
    stroke: "gray.4"
  },

  input: {
    width: [showing ? 150 : 0, 150],
    maxWidth: ["inherit", rem(400)],
    outline: "none",
    appearance: "none",
    border: 0,
    bg: "transparent",
    transition: "width .3s"
  }
});
