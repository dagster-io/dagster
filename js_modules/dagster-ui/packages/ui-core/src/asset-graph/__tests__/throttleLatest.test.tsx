import {throttleLatest} from '../throttleLatest';

jest.useFakeTimers();

describe('throttleLatest', () => {
  let mockFunction: jest.Mock<Promise<string>, [number]>;
  let throttledFunction: (arg: number) => Promise<string>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockFunction = jest.fn((arg: number) => {
      return Promise.resolve(`Result: ${arg}`);
    });
    throttledFunction = throttleLatest(mockFunction, 2000);
  });

  it('should execute the first call immediately', async () => {
    const promise = throttledFunction(1);
    expect(mockFunction).toHaveBeenCalledWith(1);

    await expect(promise).resolves.toBe('Result: 1');
  });

  it('should throttle subsequent calls within wait time and reject previous promises', async () => {
    const promise1 = throttledFunction(1);
    const promise2 = throttledFunction(2);

    await expect(promise1).rejects.toThrow('Throttled: A new call has been made.');

    expect(mockFunction).toHaveBeenCalledTimes(1);

    jest.runAllTimers();

    await expect(promise2).resolves.toBe('Result: 2');
  });

  it('should allow a new call after the wait time', async () => {
    const promise1 = throttledFunction(1);

    jest.advanceTimersByTime(1000);

    const promise2 = throttledFunction(2);

    await expect(promise1).rejects.toThrow('Throttled: A new call has been made.');

    jest.advanceTimersByTime(1000);

    await expect(promise2).resolves.toBe('Result: 2');

    const promise3 = throttledFunction(3);

    await jest.runAllTimers();

    await expect(promise3).resolves.toBe('Result: 3');

    expect(mockFunction).toHaveBeenCalledTimes(3);
    expect(mockFunction).toHaveBeenNthCalledWith(3, 3);
  });

  it('should handle multiple rapid calls correctly', async () => {
    const promise1 = throttledFunction(1);
    await Promise.resolve();

    throttledFunction(2);

    const promise3 = throttledFunction(3);

    await jest.runAllTimers();

    expect(mockFunction).toHaveBeenNthCalledWith(1, 1);
    expect(mockFunction).toHaveBeenCalledTimes(2);
    expect(mockFunction).toHaveBeenNthCalledWith(2, 3);
    await expect(promise1).resolves.toBe('Result: 1');
    await expect(promise3).resolves.toBe('Result: 3');
  });

  it('should reject the previous active promise when a new call is made before it resolves', async () => {
    // Modify mockFunction to return a promise that doesn't resolve immediately
    mockFunction.mockImplementationOnce((arg: number) => {
      return new Promise((resolve) => {
        setTimeout(() => resolve(`Result: ${arg}`), 5000);
      });
    });

    const promise1 = throttledFunction(1);

    // After 100ms, make a new call
    jest.advanceTimersByTime(100);
    const promise2 = throttledFunction(2);

    // The first promise should be rejected
    await expect(promise1).rejects.toThrow('Throttled: A new call has been made.');

    // The second promise is scheduled to execute after the remaining time (2000 - 100 = 1900ms)
    jest.advanceTimersByTime(1900);

    // Now, the second call should resolve
    await expect(promise2).resolves.toBe('Result: 2');
  });

  it('should handle function rejection correctly', async () => {
    mockFunction.mockImplementationOnce(() => {
      return Promise.reject(new Error('Function failed'));
    });

    const promise1 = throttledFunction(1);
    jest.runAllTimers();

    await expect(promise1).rejects.toThrow('Function failed');
  });

  it('should not reject promises if no new call is made within wait time', async () => {
    const promise1 = throttledFunction(1);

    // No subsequent calls
    jest.runAllTimers();

    await expect(promise1).resolves.toBe('Result: 1');
  });

  it('should handle multiple sequential calls with enough time between them', async () => {
    const promise1 = throttledFunction(1);
    jest.runAllTimers();
    await expect(promise1).resolves.toBe('Result: 1');

    const promise2 = throttledFunction(2);
    jest.runAllTimers();
    await expect(promise2).resolves.toBe('Result: 2');

    const promise3 = throttledFunction(3);
    jest.runAllTimers();
    await expect(promise3).resolves.toBe('Result: 3');

    expect(mockFunction).toHaveBeenCalledTimes(3);
  });
});
