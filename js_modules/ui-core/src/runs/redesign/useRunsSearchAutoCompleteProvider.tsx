import {IconName} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {
  RUNS_SEARCH_ATTRIBUTES,
  RUN_STATUSES,
  RunsSearchAttribute,
  TAG_KEY_BY_ATTRIBUTE,
  formatRunsSearchValue,
  tagValueToCodeLocation,
} from './runsSearchAttributes';
import {COMMON_COLLATOR} from '../../app/Util';
import {isHiddenAssetGroupJob} from '../../asset-graph/Utils';
import {
  createSelectionAutoComplete,
  useSelectionAutoCompleteResults,
} from '../../selection/SelectionAutoComplete';
import {
  SelectionAutoCompleteProvider,
  createProvider,
} from '../../selection/SelectionAutoCompleteProvider';
import {DagsterRepoOption, useRepositoryOptions} from '../../workspace/WorkspaceContext/util';
import {useLazyRunTagValues} from '../useRunTagQueries';

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

const ATTRIBUTE_LABELS = {
  id: 'Run ID',
  backfill: 'Backfill ID',
  snapshot_id: 'Snapshot ID',
} as const satisfies Partial<Record<RunsSearchAttribute, string>>;

type ValuesByAttribute = Record<RunsSearchAttribute, string[]>;

// The shared provider inserts an empty value as `<null>`, which the Runs search rejects.
const withoutEmptyValues = (values: string[]) => values.filter((value) => value !== '');

const getWorkspaceValues = (options: DagsterRepoOption[]) => {
  const jobs = options.flatMap(({repository}) =>
    repository.pipelines
      .filter((pipeline) => pipeline.isJob && !isHiddenAssetGroupJob(pipeline.name))
      .map((pipeline) => pipeline.name),
  );
  const codeLocations = options.flatMap(
    ({repository, repositoryLocation}) =>
      tagValueToCodeLocation(`${repository.name}@${repositoryLocation.name}`) ?? [],
  );

  return {
    jobs: [...new Set(jobs)].sort(COMMON_COLLATOR.compare),
    codeLocations: codeLocations.sort(COMMON_COLLATOR.compare),
  };
};

const createRunsSearchHint = (valuesByAttribute: ValuesByAttribute) =>
  createSelectionAutoComplete({
    ...createProvider({
      attributesMap: Object.fromEntries(
        RUNS_SEARCH_ATTRIBUTES.map((attribute) => [attribute, valuesByAttribute[attribute]]),
      ),
      attributeToIcon: ATTRIBUTE_ICONS,
      attributeToLabel: ATTRIBUTE_LABELS,
      functions: [],
      formatValue: formatRunsSearchValue,
    }),
    supportsTraversal: false,
    supportsNot: false,
  });

export const useRunsSearchAutoCompleteProvider = () => {
  const {options, loading: workspaceLoading} = useRepositoryOptions();

  const sensors = useLazyRunTagValues(TAG_KEY_BY_ATTRIBUTE.sensor);
  const schedules = useLazyRunTagValues(TAG_KEY_BY_ATTRIBUTE.schedule);
  const users = useLazyRunTagValues(TAG_KEY_BY_ATTRIBUTE.user);
  const backfills = useLazyRunTagValues(TAG_KEY_BY_ATTRIBUTE.backfill);
  const partitions = useLazyRunTagValues(TAG_KEY_BY_ATTRIBUTE.partition);
  const tagValueQueries = [sensors, schedules, users, backfills, partitions];

  const hint = useMemo(() => {
    const {jobs, codeLocations} = getWorkspaceValues(options);
    return createRunsSearchHint({
      status: RUN_STATUSES,
      sensor: withoutEmptyValues(sensors.values),
      schedule: withoutEmptyValues(schedules.values),
      user: withoutEmptyValues(users.values),
      job: jobs,
      code_location: codeLocations,
      id: [],
      backfill: withoutEmptyValues(backfills.values),
      partition: withoutEmptyValues(partitions.values),
      tag: [],
      snapshot_id: [],
    });
  }, [
    options,
    sensors.values,
    schedules.values,
    users.values,
    backfills.values,
    partitions.values,
  ]);

  const loading = workspaceLoading || tagValueQueries.some((query) => query.loading);

  /** Load each list once per page, retrying any that failed. */
  const fetchValues = () => {
    tagValueQueries
      .filter((query) => !query.loaded && !query.loading)
      .forEach((query) => query.fetch());
  };

  const useAutoComplete: SelectionAutoCompleteProvider['useAutoComplete'] = ({
    line,
    cursorIndex,
  }) => ({
    autoCompleteResults: useSelectionAutoCompleteResults(hint, line, cursorIndex),
    loading,
  });

  return {useAutoComplete, fetchValues};
};
