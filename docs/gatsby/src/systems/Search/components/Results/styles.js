export const wrapper = showing => ({
  p: 3,
  borderRadius: "radius",
  display: showing ? "grid" : "none",
  minWidth: ["90%", "90%", "600px"],
  maxHeight: "80vh",
  overflow: "auto",
  zIndex: 2,
  position: "absolute",
  top: "calc(100% + 5px)",
  left: 0,

  background: "white",
  boxShadow: 2,

  header: {
    my: 3,
    pb: 3,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottom: t => `1px solid ${t.colors.lightGray[2]}`
  },

  "header:first-of-type": {
    mt: 0
  },

  "header > h3": {
    m: 0,
    fontSize: 4,
    color: "primary"
  },

  "header > span": {
    fontSize: 3
  },

  ul: {
    listStyle: "none",
    p: 0,
    m: 0
  },

  "ul h4": {
    fontSize: 3,
    mb: 0
  },

  mark: {
    bg: "lightGray.1",
    color: "dark.1"
  },

  a: {
    color: "gray.1"
  },

  ".ais-Snippet": {
    fontSize: 1
  }
});

export const poweredBy = {
  display: "flex",
  alignItems: "center",
  justifyContent: "flex-end",
  py: 3,
  pb: 2,
  fontSize: 2,
  textAlign: "right",
  borderTop: t => `1px solid ${t.colors.lightGray[2]}`,

  img: {
    mb: 0,
    ml: 2
  }
};
