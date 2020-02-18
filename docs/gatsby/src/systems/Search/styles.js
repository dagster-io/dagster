export const search = {
  flex: 1,
  py: 2,
  px: 3,
  overflow: ["hidden", "auto"],
  display: "flex",
  alignItems: "center",
  fontSize: 3,
  boxShadow: "0 0 8px rgba(0,0,0,.2)",
  borderRadius: "radius",

  ":hover": {
    cursor: "pointer"
  },

  svg: {
    mr: 2,
    stroke: "blue.4"
  },

  input: {
    flex: 1, // Maybe remove
    width: "100%",
    outline: "none",
    appearance: "none",
    border: 0,
    bg: "transparent",
    transition: "width .3s",
    color: "blue.2"
  }
};

export const searchMobile = {
  display: "flex",
  alignItems: "center",

  svg: {
    mr: 2,
    stroke: "blue.4"
  }
};
