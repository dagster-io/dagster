export type ThrottledFunction<T extends (...args: any[]) => Promise<any>> = (
  ...args: Parameters<T>
) => ReturnType<T>;

export function throttleLatest<T extends (...args: any[]) => Promise<any>>(
  func: T,
  wait: number,
): ThrottledFunction<T> {
  let timeout: NodeJS.Timeout | null = null;
  let lastCallTime: number = 0;
  let activeReject: ((reason?: any) => void) | null = null;

  return function (...args: Parameters<T>): ReturnType<T> {
    const now = Date.now();

    return new Promise((resolve, reject) => {
      // If a call is already active, reject its promise
      if (activeReject) {
        activeReject(new Error('Throttled: A new call has been made.'));
        activeReject = null;
      }

      const execute = () => {
        lastCallTime = Date.now();
        activeReject = reject;

        func(...args)
          .then((result) => {
            resolve(result);
            activeReject = null;
          })
          .catch((error) => {
            reject(error);
            activeReject = null;
          });
      };

      const remaining = wait - (now - lastCallTime);
      if (remaining <= 0) {
        if (timeout) {
          clearTimeout(timeout);
          timeout = null;
        }
        execute();
      } else {
        if (timeout) {
          clearTimeout(timeout);
        }
        timeout = setTimeout(() => {
          execute();
          timeout = null;
        }, remaining);
      }
    }) as ReturnType<T>;
  };
}
