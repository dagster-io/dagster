import {CursorPaginationProps} from '@dagster-io/ui-components';
import {DocumentNode} from 'graphql';
import {History} from 'history';
import {useState} from 'react';
import {useHistory} from 'react-router-dom';

import {useQuery} from '../apollo-client';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

interface CursorPaginationQueryVariables {
  cursor?: string | null;
  limit?: number | null;
}

type SavedCursorStack = {
  cursor: string;
  stack: string[];
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isSavedCursorStack(value: unknown): value is SavedCursorStack {
  return (
    isRecord(value) &&
    typeof value.cursor === 'string' &&
    Array.isArray(value.stack) &&
    value.stack.every((item) => typeof item === 'string')
  );
}

function getSavedCursorStack(history: History, queryKey: string, cursor: string | undefined) {
  const state = history.location.state;
  const saved =
    isRecord(state) && isRecord(state.cursorStacks) ? state.cursorStacks[queryKey] : null;

  // Filter changes clear the cursor, so a matching cursor means the stack belongs to this query.
  if (cursor !== undefined && isSavedCursorStack(saved) && saved.cursor === cursor) {
    return saved.stack;
  }

  return [];
}

/**
 * Saves the stack on the current history entry so Back and reload can restore previous pages.
 * Passing `null` removes it. Other `location.state` fields are kept.
 */
function saveCursorStack(history: History, queryKey: string, saved: SavedCursorStack | null) {
  const state = isRecord(history.location.state) ? history.location.state : {};
  const {[queryKey]: _previous, ...otherStacks} = isRecord(state.cursorStacks)
    ? state.cursorStacks
    : {};
  const cursorStacks = saved ? {...otherStacks, [queryKey]: saved} : otherStacks;
  history.replace({...history.location, state: {...state, cursorStacks}});
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
  getResultArray: (result: T | undefined) => unknown[];
  nextCursorForResult: (result: T) => string | undefined;
  hasMoreForResult?: (result: T) => boolean;
}) {
  const queryKey = options.queryKey || 'cursor';
  const history = useHistory();
  const [cursor, setCursor] = useQueryPersistedState<string | undefined>({queryKey});
  const [cursorStack, setCursorStack] = useState<string[]>(() =>
    getSavedCursorStack(history, queryKey, cursor),
  );

  // If you don't provide a hasMoreForResult function for extracting hasMore from
  // the response, we fall back to an old approach that fetched one extra item
  // and used it's presence to determine if more items were available. If you use
  // the old approach, your `nextCursorForResult` method needs to use
  // `items[pageSize - 1]` NOT `items[items.length - 1]` to get the next cursor,
  // or an item will be skipped when you advance.
  //
  const limit = options.hasMoreForResult ? options.pageSize : options.pageSize + 1;
  const queryVars = {...options.variables, cursor, limit} as TVars;

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
      const prevCursor = nextStack.pop();
      setCursor(prevCursor);
      setCursorStack(nextStack);
      const saved = prevCursor ? {cursor: prevCursor, stack: nextStack} : null;
      saveCursorStack(history, queryKey, saved);
    },
    advanceCursor: () => {
      const nextStack = cursor ? [...cursorStack, cursor] : [];
      const nextCursor = queryResult.data && options.nextCursorForResult(queryResult.data);
      if (!nextCursor) {
        return;
      }
      setCursorStack(nextStack);
      setCursor(nextCursor);
      saveCursorStack(history, queryKey, {cursor: nextCursor, stack: nextStack});
    },
    reset: () => {
      setCursorStack([]);
      setCursor(undefined);
      saveCursorStack(history, queryKey, null);
    },
  };

  return {queryResult, paginationProps};
}
