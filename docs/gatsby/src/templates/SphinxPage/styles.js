export const wrapper = {
  display: "flex",
  height: "100%"
};

export const content = {
  flex: 1,
  px: [3, 4, 6],
  maxWidth: ["100%", "100%", "calc(100% - 280px)"]
};

export const icon = {
  mr: 1
};

export const btnShowToc = {
  my: 3,
  py: 1,
  px: 2,
  borderRadius: "radius",
  appearance: "none",
  border: t => `1px solid ${t.colors.lightGray[1]}`,
  bg: "lightGray.3",
  display: "flex",
  alignItems: "center",
  textTransform: "uppercase",
  fontSize: 12,
  fontWeight: "bold",
  color: "gray.1"
};

export const pageLinks = {
  display: "flex",
  justifyContent: "space-between",
  pt: [2, 3, 3],
  mt: [2, 3, 3],
  mb: 2,
  borderTop: t => `1px solid ${t.colors.lightGray[1]}`,

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

export const breadcrumb = {
  listStyle: "none",
  p: 0,
  m: 0,
  pb: [2, 3, 3],
  mb: [2, 3, 3],
  borderBottom: t => `1px solid ${t.colors.lightGray[1]}`,
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
