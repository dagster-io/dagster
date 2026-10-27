import {IconName} from '@dagster-io/ui-components';

import {RUNS_SEARCH_ATTRIBUTES, RunsSearchAttribute} from './runsSearchAttributes';
import {
  createSelectionAutoComplete,
  useSelectionAutoCompleteResults,
} from '../../selection/SelectionAutoComplete';
import {
  SelectionAutoCompleteProvider,
  createProvider,
} from '../../selection/SelectionAutoCompleteProvider';

const ATTRIBUTE_ICONS = {
  id: 'id',
  status: 'status',
  job: 'job',
  code_location: 'code_location',
  sensor: 'sensors',
  schedule: 'schedule',
  user: 'account_circle',
  backfill: 'backfill',
  partition: 'partition',
  tag: 'tag',
  snapshot_id: 'snapshot',
} as const satisfies Record<RunsSearchAttribute, IconName>;

// Suggests attribute names only; value suggestions need workspace and run data.
const getRunsSearchHint = createSelectionAutoComplete({
  ...createProvider({
    attributesMap: Object.fromEntries(RUNS_SEARCH_ATTRIBUTES.map((attribute) => [attribute, []])),
    attributeToIcon: ATTRIBUTE_ICONS,
    functions: [],
  }),
  supportsTraversal: false,
  supportsNot: false,
});

export const useRunsSearchAutoComplete: SelectionAutoCompleteProvider['useAutoComplete'] = ({
  line,
  cursorIndex,
}) => {
  const autoCompleteResults = useSelectionAutoCompleteResults(getRunsSearchHint, line, cursorIndex);
  return {autoCompleteResults, loading: false};
};
