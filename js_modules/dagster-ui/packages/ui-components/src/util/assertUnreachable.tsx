export const assertUnreachable = (_: any): any => {
  throw new Error("Didn't expect to get here");
};
