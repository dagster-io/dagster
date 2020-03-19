import { SxStyleProp } from "theme-ui";

export const wrapper: SxStyleProp = {
  "&, &:visited, &:active": {
    color: "primary"
  },
  ":hover": {
    color: "blue.4"
  }
};
