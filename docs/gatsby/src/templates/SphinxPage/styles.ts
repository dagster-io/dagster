import { SxStyleProp, Theme } from "theme-ui";
import { ColorPallette } from "gatsby-plugin-theme-ui/types";

export const wrapper: SxStyleProp = {
  display: "flex",
  height: "100%"
};

export const content: SxStyleProp = {
  flex: 1,
  px: [3, 4, 6],
  maxWidth: ["100%", "100%", "calc(100% - 280px)"]
};

export const icon: SxStyleProp = {
  mr: 1
};

export const btnShowToc: SxStyleProp = {
  my: 3,
  py: 1,
  px: 2,
  borderRadius: "radius",
  appearance: "none",
  border: (t: Theme) => `1px solid ${t.colors!.lightGray as ColorPallette[1]}`,
  bg: "lightGray.3",
  display: "flex",
  alignItems: "center",
  textTransform: "uppercase",
  fontSize: 12,
  fontWeight: "bold",
  color: "gray.1"
};

export const pageLinks: SxStyleProp = {
  display: "flex",
  justifyContent: "space-between",
  pt: [2, 3, 3],
  mt: [2, 3, 3],
  mb: 2,
  borderTop: (t: Theme) =>
    `1px solid ${t.colors!.lightGray as ColorPallette[1]}`,

  a: {
    display: "inline-flex",
    alignItems: "center",
    border: "1px solid",
    padding: "10px 20px"
  },

  svg: {
    stroke: "gray.1"
  },

  "svg.left": {
    mr: 2
  },
  "svg.right": {
    ml: 2
  }
};

export const breadcrumb: SxStyleProp = {
  listStyle: "none",
  p: 0,
  m: 0,
  pb: [2, 3, 3],
  mb: [2, 3, 3],
  borderBottom: (t: Theme) =>
    `1px solid ${t.colors!.lightGray as ColorPallette[1]}`,
  display: "flex",
  fontSize: 2,

  li: {
    m: 0
  },

  "li ~ li": {
    ml: 2
  },

  "li:not(:first-of-type)::before": {
    display: "inline-block",
    content: '"|"',
    mr: 2,
    color: "gray.3"
  },

  "li.current": {
    color: "gray.2"
  },

  "li, li a": {
    display: "flex",
    alignItems: "center"
  }
};
