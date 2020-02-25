import { theme as t } from "utils/css";

export const page = state => {
  const closed = !state.matches("showing");
  const transform = `translate(${closed ? "-250px" : 0})`;

  return {
    display: "flex",
    width: "calc(100% + 250px)",
    transform: [transform, transform, "none"],
    transition: "transform .3s",
    height: "100%",
    pt: 4
  };
};

export const content = state => {
  const closed = !state.matches("showing");
  return {
    flex: 1,
    mt: 0,

    maxWidth: [
      "calc(100% - 250px)",
      "calc(100% - 250px)",
      "calc(100% - 500px)"
    ],

    ...(state.context.width < 1024 && {
      "::after": {
        display: "block",
        position: "absolute",
        content: '""',
        top: closed ? "-100%" : 0,
        left: 0,
        width: "100%",
        height: "100%",
        bg: "white",
        opacity: closed ? 0 : 0.8,
        transition: "all .3s"
      }
    })
  };
};
