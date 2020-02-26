export const wrapper = {
  m: 0,

  "&.active.toctree-l1": {
    mb: 2,
    fontSize: 2
  },
  "&.toctree-l1 a": {
    fontWeight: 600,
    fontSize: "18px",
    color: "#A59898 !important"
  },
  "&.active.toctree-l1 a": {
    color: "black !important"
  },
  "&.active.toctree-l1 ul": {
    borderLeft: "1px solid #C4C4C4",
    marginLeft: "3px",
    marginTop: "8px",
    paddingLeft: "15px"
  },
  "&:not(.active) > ul": {
    display: "none"
  },
  "&.toctree-l2": {
    lineHeight: 1.1,
    whiteSpace: "normal",
    marginTop: ".4em",
    padding: ".1em"
  },
  "&.toctree-l2.active": {
    color: "#2491EB !important",
    position: "relative"
  },
  "&.toctree-l2 a": {
    fontWeight: 400,
    fontSize: 1,
    opacity: 0.6
  },
  "&.toctree-l2 a:hover, &.toctree-l2 a.active": {
    opacity: 1,
    fontWeight: 400
  },

  "&.toctree-l2 a.active": {
    color: "#2491EB !important",
    fontWeight: 600
  },
  "&.toctree-l2 > ul": {
    display: "none"
  }
};
