import {useEffect, useRef, useState} from 'react';

interface State<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
}

/**
 * A hook that fetches data from a function that might throw a promise, without suspending.
 * It manages the asynchronous loading state and updates the component with data or error.
 * @param dataFetcher A function that might throw a promise when called, returning the data directly or through a promise.
 * @returns An object containing the data, the error if any, and the loading state.
 */
export function useSuspensefulDataWithoutSuspending<T>(dataFetcher: () => T): State<T> {
  const [state, setState] = useState<State<T>>({
    data: null,
    error: null,
    loading: true,
  });
  const hasCancelled = useRef(false);

  useEffect(() => {
    // Reset state when the dataFetcher changes
    setState({data: null, error: null, loading: true});

    // Function to safely set state if the component is still mounted
    const safeSetState = (newState: State<T>) => {
      if (!hasCancelled.current) {
        setState(newState);
      }
    };

    try {
      const result = dataFetcher();
      // If no promise is thrown and result is available directly
      safeSetState({data: result, error: null, loading: false});
    } catch (error) {
      if (error instanceof Promise) {
        // Subscribe to the thrown promise
        error.then(
          (_) => safeSetState({data: dataFetcher(), error: null, loading: false}),
          (error) => safeSetState({data: null, error, loading: false}),
        );
      } else {
        // It's an actual error, not a promise
        safeSetState({
          data: null,
          error: error instanceof Error ? error : new Error('An unexpected error occurred'),
          loading: false,
        });
      }
    }

    return () => {
      hasCancelled.current = true;
    };
  }, [dataFetcher]);

  return state;
}
