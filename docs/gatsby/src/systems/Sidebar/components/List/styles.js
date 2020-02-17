export const wrapper = {
  m: 0,

  "&.active.toctree-l1": {
    mb: 2
  },
  "&:not(.active) > ul": {
    display: "none"
  },
  "&.toctree-l2": {
    fontWeight: "100",
    fontSize: 0,
    lineHeight: 1.7,
    width: 200,
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis"
  },
  "&.toctree-l2 a": {
    fontSize: 0,
    opacity: 0.4
  },
  "&.toctree-l2 a:hover": {
    opacity: 1
  },
  "&.toctree-l2 > ul": {
    display: "none"
  }
  // "&.toctree-l2:after": {
  //   display: "inline-block",
  //   content: '"  ●"',
  //   ml: 1
  // }
};
