export const firstBlock = {
  m: "0 auto",
  maxWidth: 424,
  textAlign: "center",

  h1: {
    fontSize: 6
  },
  "h1 span": {
    color: "primary"
  }
};

export const secondBlock = {
  display: "grid",
  gridGap: 4,
  gridTemplateColumns: ["1fr", "repeat(3, 1fr)", "repeat(3, 1fr)"],
  mt: 4,
  mx: 4,

  img: {
    mb: 2
  },

  h2: {
    fontSize: 2
  },

  p: {
    color: "gray.1",
    fontSize: 2
  }
};
