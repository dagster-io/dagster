import {
  TokenizingFieldValue,
  tokenizedValuesFromStringArray,
  tokensAsStringArray,
} from '@dagster-io/ui-components';
import qs from 'qs';
import {useMemo} from 'react';

import {RUNS_FEED_CURSOR_KEY} from './RunsFeedUtils';
import {RunStatus, RunsFeedView, RunsFilter} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

export type RunFilterTokenType =
  | 'id'
  | 'status'
  | 'pipeline'
  | 'partition'
  | 'job'
  | 'snapshotId'
  | 'tag'
  | 'backfill'
  | 'created_date_before'
  | 'created_date_after';

export type RunFilterToken = {
  token?: RunFilterTokenType;
  value: string;
};

const RUN_PROVIDERS_EMPTY = [
  {token: 'id', values: () => []},
  {token: 'status', values: () => []},
  {token: 'pipeline', values: () => []},
  {token: 'job', values: () => []},
  {token: 'tag', values: () => []},
  {token: 'snapshotId', values: () => []},
  {token: 'created_date_before', values: () => []},
  {token: 'created_date_after', values: () => []},
];

/** Persist run filters in the URL and clear pagination when they change. */
export function useQueryPersistedRunFilters(enabledFilters?: RunFilterTokenType[]) {
  return useQueryPersistedState<RunFilterToken[]>(
    useMemo(
      () => ({
        encode: (tokens) => ({
          q: tokensAsStringArray(tokens),
          cursor: undefined,
          [RUNS_FEED_CURSOR_KEY]: undefined,
        }),
        decode: ({q}) => {
          const values = (Array.isArray(q) ? q : []).map(String);
          return tokenizedValuesFromStringArray(values, RUN_PROVIDERS_EMPTY).filter(
            (t) =>
              !t.token || !enabledFilters || enabledFilters.includes(t.token as RunFilterTokenType),
          ) as RunFilterToken[];
        },
      }),
      [enabledFilters],
    ),
  );
}

export function runsPathWithFilters(
  filterTokens: RunFilterToken[],
  basePath: string = '/runs',
  view?: RunsFeedView,
) {
  return `${basePath}?${qs.stringify(
    {q: tokensAsStringArray(filterTokens), view: view?.toLowerCase()},
    {arrayFormat: 'brackets'},
  )}`;
}

export function runsFilterForSearchTokens(search: TokenizingFieldValue[]) {
  if (!search[0]) {
    return {};
  }

  const obj: RunsFilter = {};

  for (const item of search) {
    if (item.token === 'created_date_before') {
      obj.createdBefore = parseInt(item.value);
    } else if (item.token === 'created_date_after') {
      obj.createdAfter = parseInt(item.value);
    } else if (item.token === 'pipeline' || item.token === 'job') {
      obj.pipelineName = item.value;
    } else if (item.token === 'id') {
      obj.runIds = obj.runIds || [];
      obj.runIds.push(item.value);
    } else if (item.token === 'status') {
      obj.statuses = obj.statuses || [];
      obj.statuses.push(item.value as RunStatus);
    } else if (item.token === 'snapshotId') {
      obj.snapshotId = item.value;
    } else if (item.token === 'tag') {
      const [key = '', value = ''] = item.value.split('=');
      if (obj.tags) {
        obj.tags.push({key, value});
      } else {
        obj.tags = [{key, value}];
      }
    }
  }

  return obj;
}
