import {TokenizingFieldValue} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import qs from 'qs';

import {failedStatuses, inProgressStatuses, queuedStatuses} from './RunStatuses';
import {RunsFeedView} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

export const RUNS_FEED_CURSOR_KEY = `runs_before`;

export function getBackfillPath(id: string, tab?: 'runs') {
  return tab ? `/runs/b/${id}?tab=${tab}` : `/runs/b/${id}`;
}

// Module-level so the setter stays stable across renders.
const encodeRunsFeedView = (view: RunsFeedView) => ({
  view: view && view !== RunsFeedView.ROOTS ? view.toLowerCase() : undefined,
});

const decodeRunsFeedView = (query: qs.ParsedQs) => {
  const value = typeof query.view === 'string' ? query.view : RunsFeedView.ROOTS;
  return value.toUpperCase() as RunsFeedView;
};

export const useQueryPersistedRunsFeedView = () =>
  useQueryPersistedState<RunsFeedView>({
    encode: encodeRunsFeedView,
    decode: decodeRunsFeedView,
  });

export const getSelectedRunsFeedTab = (
  filterTokens: TokenizingFieldValue[],
  view: RunsFeedView,
) => {
  if (view === RunsFeedView.BACKFILLS) {
    return 'backfills';
  }
  const statusTokens = new Set(
    filterTokens.filter((token) => token.token === 'status').map((token) => token.value),
  );
  if (isEqual(queuedStatuses, statusTokens)) {
    return 'queued';
  }
  if (isEqual(inProgressStatuses, statusTokens)) {
    return 'in-progress';
  }
  if (isEqual(failedStatuses, statusTokens)) {
    return 'failed';
  }
  return 'all';
};

type SelectedTab = ReturnType<typeof getSelectedRunsFeedTab>;

export const getRunsFeedDocumentTitle = (selected: SelectedTab) => {
  switch (selected) {
    case 'all':
      return 'Runs | All';
    case 'backfills':
      return 'Runs | All backfills';
    case 'failed':
      return 'Runs | Failed';
    case 'in-progress':
      return 'Runs | In progress';
    case 'queued':
      return 'Runs | Queued';
    default:
      return 'Runs';
  }
};

// Include runs inside backfills in the queued and in-progress tabs.
export const getRunsFeedQueryView = (selectedTab: SelectedTab, view: RunsFeedView) =>
  selectedTab === 'queued' || selectedTab === 'in-progress' ? RunsFeedView.RUNS : view;
