import {
  LazyQueryHookOptions,
  OperationVariables,
  QueryHookOptions,
  useLazyQuery as useLazyQueryApollo,
  useQuery as useQueryApollo,
} from '@apollo/client';

import {useBlockTraceOnQueryResult} from '../performance/TraceContext';

export * from '@apollo/client';

interface ExtendedQueryOptions<TData = any, TVariables extends OperationVariables = any>
  extends QueryHookOptions<TData, TVariables> {
  blocking?: boolean;
}

interface ExtendedLazyQueryOptions<TData = any, TVariables extends OperationVariables = any>
  extends LazyQueryHookOptions<TData, TVariables> {
  blocking?: boolean;
}

export function useQuery<TData = any, TVariables extends OperationVariables = any>(
  query: any,
  options?: ExtendedQueryOptions<TData, TVariables>,
) {
  const {blocking = true, ...restOptions} = options || {};
  const queryResult = useQueryApollo<TData, TVariables>(query, restOptions);
  useBlockTraceOnQueryResult(queryResult, 'graphql', {
    skip: !blocking,
  });
  return queryResult;
}

export function useLazyQuery<TData = any, TVariables extends OperationVariables = any>(
  query: any,
  options?: ExtendedLazyQueryOptions<TData, TVariables>,
) {
  const {blocking = true, ...restOptions} = options || {};
  const result = useLazyQueryApollo<TData, TVariables>(query, restOptions);
  useBlockTraceOnQueryResult(result[1], 'graphql', {
    skip: !blocking,
  });
  return result;
}
