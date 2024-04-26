import {assertUnreachable} from '../app/Util';

// Wrap a promise to make it Suspense compatible
export function wrapPromise<T extends {data?: any}>(promise: Promise<T>) {
  let status: 'success' | 'pending' | 'error' = 'pending';
  let result: T | Error;
  const suspender = promise.then(
    (r) => {
      status = 'success';
      result = r;
    },
    (e) => {
      status = 'error';
      result = e;
      console.log('set error', e);
    },
  );
  return {
    read() {
      if (status === 'pending') {
        throw suspender;
      } else if (status === 'error') {
        throw result;
      } else if (status === 'success') {
        return (result as T).data;
      } else {
        assertUnreachable(status);
      }
    },
  };
}
