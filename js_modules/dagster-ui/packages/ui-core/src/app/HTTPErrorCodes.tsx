export const ERROR_CODES_TO_SURFACE = new Set([
  504, // Gateway timeout
]);

export const errorCodeToMessage = (statusCode: number) => {
  switch (statusCode) {
    case 504:
      return '请求超时，请查看控制台详情';
    default:
      return '发生网络错误，请查看控制台详情';
  }
};
