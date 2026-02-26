import {CursorPaginationProps} from '@dagster-io/ui-components';
import {DocumentNode} from 'graphql';
import {useState} from 'react';

import {useQuery} from '../apollo-client';
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
  skip?: boolean;
  variables: Omit<TVars, 'cursor' | 'limit'>;
  pageSize: number;
  queryKey?: string;
  getResultArray: (result: T | undefined) => any[];
  nextCursorForResult: (result: T) => string | undefined;
  hasMoreForResult?: (result: T) => boolean;
}) {
  const [cursorStack, setCursorStack] = useState<string[]>(() => []);
  const [cursor, setCursor] = useQueryPersistedState<string | undefined>({
    queryKey: options.queryKey || 'cursor',
  });

  // If you don't provide a hasMoreForResult function for extracting hasMore from
  // the response, we fall back to an old approach that fetched one extra item
  // and used it's presence to determine if more items were available. If you use
  // the old approach, your `nextCursorForResult` method needs to use
  // `items[pageSize - 1]` NOT `items[items.length - 1]` to get the next cursor,
  // or an item will be skipped when you advance.
  //
  const limit = options.hasMoreForResult ? options.pageSize : options.pageSize + 1;
  const queryVars: any = {...options.variables, cursor, limit};

  const queryResult = useQuery<T, TVars>(options.query, {
    skip: options.skip,
    variables: queryVars,
    notifyOnNetworkStatusChange: true,
  });

  const resultArray = options.getResultArray(queryResult.data);

  let hasNextCursor = false;
  if (options.hasMoreForResult) {
    hasNextCursor = queryResult.data ? options.hasMoreForResult(queryResult.data) : false;
  } else {
    hasNextCursor = resultArray.length === options.pageSize + 1;
  }

  const paginationProps: CursorPaginationProps = {
    cursor,
    hasPrevCursor: !!cursor,
    hasNextCursor,
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
