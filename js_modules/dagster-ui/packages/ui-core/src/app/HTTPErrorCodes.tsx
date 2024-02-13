export const ERROR_CODES_TO_SURFACE = new Set([
  504, // Gateway timeout
]);

export const errorCodeToMessage = (statusCode: number) => {
  switch (statusCode) {
    case 504:
      return 'Request timed out. See console for details.';
    default:
      return 'A network error occurred. See console for details.';
  }
};
