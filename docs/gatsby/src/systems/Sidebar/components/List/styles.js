export const wrapper = {
  m: 0,

  "&.active.toctree-l1": {
    mb: 2,
    fontSize: 3
  },
  "&.toctree-l1 a": {
    fontWeight: 800,
    fontSize: "18px",
    color: "#A59898 !important"
  },
  "&.active.toctree-l1 a": {
    color: "black !important"
  },
  "&.active.toctree-l1 ul": {
    borderLeft: "1px solid #A59898",
    paddingLeft: "15px"
  },
  "&:not(.active) > ul": {
    display: "none"
  },
  "&.toctree-l2": {
    fontSize: 0,
    whiteSpace: "normal"
  },
  "&.toctree-l2 a": {
    fontSize: "16px",
    fontWeight: 400
  },
  "&.toctree-l2 a:hover, &.toctree-l2 a.active": {
    opacity: 1
  },
  "&.toctree-l2 > ul": {
    display: "none"
  }
};
