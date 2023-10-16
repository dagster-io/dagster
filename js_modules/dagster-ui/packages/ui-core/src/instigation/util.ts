const TRUNCATION_THRESHOLD = 100;
const TRUNCATION_BUFFER = 5;

export const truncate = (str: string) =>
  str.length > TRUNCATION_THRESHOLD
    ? `${str.slice(0, TRUNCATION_THRESHOLD - TRUNCATION_BUFFER)}…`
    : str;
