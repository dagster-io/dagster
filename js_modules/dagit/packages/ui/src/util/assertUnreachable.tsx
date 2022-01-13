export const assertUnreachable = (_: never): never => {
  throw new Error("Didn't expect to get here");
};
