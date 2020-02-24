export const wrapper = opened => ({
  zIndex: opened ? 99 : "auto",
  position: "relative",
  overflowY: "auto",
  py: 3,
  px: 4,
  width: 250,
  minHeight: "100vh",
  bg: "sidebar.bg",
  color: "sidebar.color",
  textAlign: "left",

  ".toctree-wrapper": {
    fontFamily: "heading",
    fontWeight: 500,
    marginRight: "16px",
    marginLeft: "16px"
  },

  ".toctree-wrapper ul": {
    m: 0,
    p: 0,
    listStyle: "none",
    color: "white"
  },

  ".version-wrapper": {
    marginLeft: "16px"
  }
});

export const active = (hasActive, top) => ({
  position: "absolute",
  width: 4,
  height: 25,
  bg: "white",
  borderRadius: "0 3px 3px 0",
  opacity: hasActive ? 1 : 0,
  top: 0,
  left: 0,
  transform: `translateY(${top - 3}px)`,
  transition: "transform .2s cubic-bezier(.25,.75,.5,1.25)"
});

export const content = {
  display: "flex",
  flexDirection: "column",
  alignItems: "flex-start",
  height: "100%",
  maxHeight: "100vh",
  pt: 3
};

export const menu = {
  mb: 4
};
