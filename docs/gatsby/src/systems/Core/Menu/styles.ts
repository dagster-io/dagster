import { SxStyleProp } from "theme-ui";

export const wrapper = (
  gap: string | number,
  vertical: boolean
): SxStyleProp & { gridGap: string | number } => ({
  display: "inline-grid",
  gridGap: gap,
  gridAutoFlow: vertical ? "row" : "column"
});
