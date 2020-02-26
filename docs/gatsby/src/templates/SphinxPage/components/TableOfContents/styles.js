import { theme as t } from "utils/css";

export const wrapper = isMobile => ({
  pr: 4,
  // ml: 4,
  mt: 0,
  width: 250,
  minWidth: 250,
  bg: "white",

  ul: {
    p: 0,
    pl: 2,
    m: 0,
    ml: 2
  },

  li: {
    margin: 0,
    fontSize: 14
  },

  "a, a.permalink": {
    color: "dark",
    opacity: 0.6
  },

  "a:hover": {
    opacity: 1
  },

  ...(isMobile && {
    m: 0,
    py: 4,
    boxShadow: "0 0 50px rgba(0,0,0,0.3)"
  })
});

export const title = {
  display: "flex",
  alignItems: "center",
  textTransform: "uppercase",
  fontSize: 12,
  color: "dark.3",
  mb: 3
};

export const icon = {
  mr: 2,
  stroke: "gray.2"
};

export const mobileWrapper = opened => ({
  position: "absolute",
  top: 0,
  display: opened ? "flex" : "none",
  flexDirection: "row-reverse",
  minWidth: "100vw",
  minHeight: "100%",
  pt: t("header.gutter"),
  bg: "rgba(0,0,0,.5)"
});
