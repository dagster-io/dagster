import {ApolloQueryResult, OperationVariables, QueryOptions, useApolloClient} from '@apollo/client';
import {useMemo} from 'react';

import {wrapPromise} from '../utils/wrapPromise';

// Default post-process function assumes TResult can be derived directly from TQuery's data
const defaultPostProcess = async <TQuery, TResult = any>(
  result: ApolloQueryResult<TQuery>,
): Promise<TResult> => {
  return result as any;
};

export function useWrappedQuery<
  TQuery,
  TVariables extends OperationVariables = OperationVariables,
  TResult = ApolloQueryResult<TQuery>,
>(
  options: QueryOptions<TVariables, TQuery>,
  postProcess: (result: ApolloQueryResult<TQuery>) => Promise<TResult> = defaultPostProcess as any,
) {
  const client = useApolloClient();
  return useMemo(() => {
    const promise = new Promise<TResult>((resolve, reject) => {
      client
        .query<TQuery, TVariables>(options)
        .then((result) => postProcess(result))
        .then((processed) => resolve(processed))
        .catch((error) => reject(error));
    });

    return wrapPromise<TResult>(promise);
  }, [client, options, postProcess]);
}
