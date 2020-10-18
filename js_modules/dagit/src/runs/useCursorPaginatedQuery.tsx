import {DocumentNode} from 'graphql';
import * as querystring from 'query-string';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {__RouterContext as RouterContext} from 'react-router';

import {CursorPaginationProps} from 'src/CursorControls';

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
  const {history, location} = React.useContext(RouterContext);
  const qs = querystring.parse(location.search);

  const [cursorStack, setCursorStack] = React.useState<string[]>([]);
  const cursor = (qs.cursor as string) || undefined;

  const setCursor = (cursor: string | undefined) => {
    history.push({search: `?${querystring.stringify({...qs, cursor})}`});
  };

  const queryVars: any = {
    ...options.variables,
    cursor: cursor,
    limit: options.pageSize + 1,
  };

  const queryResult = useQuery<T, TVars>(options.query, {
    fetchPolicy: 'cache-and-network',
    pollInterval: 15 * 1000,
    partialRefetch: true,
    variables: queryVars,
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
        setCursorStack([...cursorStack, cursor]);
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
