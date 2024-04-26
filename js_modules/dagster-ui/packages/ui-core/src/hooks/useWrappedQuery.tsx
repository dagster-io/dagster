import {OperationVariables, QueryOptions, useApolloClient} from '@apollo/client';
import {useMemo} from 'react';

import {wrapPromise} from '../utils/wrapPromise';

export function useWrappedQuery<TQuery, TVariables extends OperationVariables = OperationVariables>(
  options: QueryOptions<TVariables, TQuery>,
) {
  const client = useApolloClient();
  return useMemo(() => {
    return wrapPromise(client.query<TQuery, TVariables>(options));
  }, [client, options]);
}
