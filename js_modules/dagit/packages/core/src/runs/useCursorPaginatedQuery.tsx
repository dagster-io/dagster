import {useQuery} from '@apollo/client';
import {CursorPaginationProps} from '@dagster-io/ui';
import {DocumentNode} from 'graphql';
import * as React from 'react';

import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

interface CursorPaginationQueryVariables {
  cursor?: string | null;
  limit?: number | null;
}

/**
 * This is a React hook that makes it easier to build paginated list views based on a GraphQL
 * query. It is intended to be used in place of Apollo's `useQuery` and assumes that the query
 * takes at least `cursor` and `limit` variables. It manages those two variables internally,
 * and you can pass additional variables via the options.
 *
 * The current pagination "cursor" is saved to the URL query string, which allows the user to
 * navigate "back" in their browser history to move to previous pages.
 *
 * The returned paginationProps expose methods for moving to the next / previous page and are
 * used by <CursorPaginationControls /> to render the pagination buttons.
 */
export function useCursorPaginatedQuery<T, TVars extends CursorPaginationQueryVariables>(options: {
  query: DocumentNode;
  nextCursorForResult: (result: T) => string | undefined;
  variables: Omit<Omit<TVars, 'cusor'>, 'limit'>;
  pageSize: number;
  getResultArray: (result: T | undefined) => any[];
}) {
  const [cursorStack, setCursorStack] = React.useState<string[]>(() => []);
  const [cursor, setCursor] = useQueryPersistedState<string | undefined>({queryKey: 'cursor'});

  const queryVars: any = {
    ...options.variables,
    cursor,
    limit: options.pageSize + 1,
  };

  const queryResult = useQuery<T, TVars>(options.query, {
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    variables: queryVars,
    notifyOnNetworkStatusChange: true,
  });

  const resultArray = options.getResultArray(queryResult.data);
  const paginationProps: CursorPaginationProps = {
    hasPrevCursor: !!cursor,
    hasNextCursor: resultArray.length === options.pageSize + 1,
    popCursor: () => {
      const nextStack = [...cursorStack];
      setCursor(nextStack.pop());
      setCursorStack(nextStack);
    },
    advanceCursor: () => {
      if (cursor) {
        setCursorStack((current) => [...current, cursor]);
      }
      const nextCursor = queryResult.data && options.nextCursorForResult(queryResult.data);
      if (!nextCursor) {
        return;
      }
      setCursor(nextCursor);
    },
    reset: () => {
      setCursorStack([]);
      setCursor(undefined);
    },
  };

  return {queryResult, paginationProps};
}
