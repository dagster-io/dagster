const headingColor = {
  h1: "dark",
  h2: "dark",
  h3: "dark",
  h4: "dark",
  h5: "dark",
  h6: "dark"
};

export const wrapper = tag => ({
  position: "relative",
  display: "table",
  fontFamily: "heading",
  color: headingColor[tag],

  ".permalink": {
    position: "absolute",
    color: "inherit",
    top: 0,
    right: 0,
    transform: "translateX(130%) scale(0.8)",
    opacity: 0,
    transition: "opacity .3s"
  },

  ":hover .permalink": {
    opacity: 0.6
  }
});
