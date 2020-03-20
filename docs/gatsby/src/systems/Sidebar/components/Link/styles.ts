import { SxStyleProp } from "theme-ui";

export const link: SxStyleProp = {
  fontFamily: "heading",
  fontWeight: 500,
  opacity: 0.6,
  color: "white !important",
  fontSize: 2,

  "&.active": {
    opacity: 1
  }
};
