export const wrapper = {
  borderRadius: 0,
  position: "relative",
  paddingLeft: "75px",

  "> code": {
    p: 3,
    m: 0,
    borderRadius: 0,
    color: "dark.4",
    border: t => {
      return `1px solid ${t.colors.lightGray[1]}`;
    }
  },

  "div.viewcode-block > a.permalink": {
    position: "absolute",
    left: "0px",
    zIndex: 0
  }
};
