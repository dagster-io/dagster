import { SxStyleProp } from "theme-ui";

// TODO: Maybe send a PR to typings to fix this gridGap missing prop.
export const wrapper: SxStyleProp & { gridGap: number } = {
  position: "relative",
  display: "grid",
  gridGap: 2
};
