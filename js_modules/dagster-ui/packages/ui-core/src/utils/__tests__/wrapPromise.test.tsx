import {wrapPromise} from '../wrapPromise';

describe('wrapPromise', () => {
  it('should throw suspender when status is pending', () => {
    const testPromise = new Promise(() => {});
    const wrapped = wrapPromise(testPromise as any);
    expect(() => wrapped.read()).toThrow();
  });

  it('should throw an error when the promise is rejected', async () => {
    const testError = new Error('test error');
    const testPromise = Promise.reject(testError);
    const wrapped = wrapPromise(testPromise);

    // Pending because rejection wasn't handled yet
    try {
      wrapped.read();
    } catch (e) {
      // eslint-disable-next-line jest/no-conditional-expect
      expect(e).toBeInstanceOf(Promise);
    }

    // Flush microtask queue so that wrapPromise's `.then` on the testPromise fires first.
    await new Promise((res) => {
      setTimeout(res, 1);
    });

    expect(() => {
      wrapped.read();
    }).toThrow(testError);
  });

  it('should return data when the promise is resolved', async () => {
    const testData = {data: 'test data'};
    const testPromise = Promise.resolve(testData);
    const wrapped = wrapPromise(testPromise);

    // Wait for promise to resolve
    await Promise.resolve();

    expect(wrapped.read()).toBe(testData.data);
  });

  it('should handle multiple reads after the promise resolves', async () => {
    const testData = {data: 'test data'};
    const testPromise = Promise.resolve(testData);
    const wrapped = wrapPromise(testPromise);

    // Wait for promise to resolve
    await Promise.resolve();

    expect(wrapped.read()).toBe(testData.data);
    expect(wrapped.read()).toBe(testData.data); // Confirm it can be read multiple times without issue
  });
});
