export const wrapper = {
  m: 0,

  "&.active.toctree-l1": {
    mb: 2,
    fontSize: 3
  },
  "&:not(.active) > ul": {
    display: "none"
  },
  "&.toctree-l2": {
    fontSize: 0,
    whiteSpace: "normal"
  },
  "&.toctree-l2 a": {
    fontSize: 2,
    opacity: 1
  },
  "&.toctree-l2 a:hover": {
    opacity: 1
  },
  "&.toctree-l2 > ul": {
    display: "none"
  }
};
