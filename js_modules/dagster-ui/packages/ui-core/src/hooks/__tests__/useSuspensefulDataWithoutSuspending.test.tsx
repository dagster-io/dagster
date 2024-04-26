import {renderHook} from '@testing-library/react-hooks';

import {useSuspensefulDataWithoutSuspending} from '../useSuspensefulDataWithoutSuspending';

describe('useSuspensefulDataWithoutSuspending', () => {
  it('should initially set loading to true and data and error to null', async () => {
    const dataFetcher = () => {
      throw new Promise(() => {});
    };
    const {result} = renderHook(() => useSuspensefulDataWithoutSuspending(dataFetcher));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('should handle a dataFetcher that resolves with data', async () => {
    const dataFetcher = () => {
      throw Promise.resolve('Test Data');
    };
    const {result, waitForNextUpdate} = renderHook(() =>
      useSuspensefulDataWithoutSuspending(dataFetcher),
    );

    await waitForNextUpdate();
    expect(result.current.loading).toBe(false);
    expect(result.current.data).toBe('Test Data');
    expect(result.current.error).toBeNull();
  });

  it('should handle a dataFetcher that rejects with an error', async () => {
    const error = new Error('Failed to fetch');
    const dataFetcher = () => {
      throw Promise.reject(error);
    };
    const {result, waitForNextUpdate} = renderHook(() =>
      useSuspensefulDataWithoutSuspending(dataFetcher),
    );

    await waitForNextUpdate();

    expect(result.current.loading).toBe(false);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe(error);
  });

  it('should set loading to false if dataFetcher returns data directly', async () => {
    const dataFetcher = () => 'Direct Data';
    const {result} = renderHook(() => useSuspensefulDataWithoutSuspending(dataFetcher));

    expect(result.current.loading).toBe(false);
    expect(result.current.data).toBe('Direct Data');
    expect(result.current.error).toBeNull();
  });

  it('should not update state after the component is unmounted', async () => {
    const dataFetcher = () => {
      throw new Promise<string>((resolve) => setTimeout(() => resolve('Delayed Data'), 500));
    };
    const {result, unmount, waitForNextUpdate} = renderHook(() =>
      useSuspensefulDataWithoutSuspending(dataFetcher),
    );

    setTimeout(() => unmount(), 100);
    try {
      await waitForNextUpdate();
    } catch (e) {
      // Expecting an error because the update should not occur after unmount
    }

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });
});
