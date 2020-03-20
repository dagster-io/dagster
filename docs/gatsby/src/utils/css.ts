import * as R from "ramda";

export const theme = (str: string) => R.path(str.split("."));
export const rem = (val: number) => `${val / 18}rem`;
