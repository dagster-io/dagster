import {Box, Colors, Icon, Spinner, Subheading} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import uniq from 'lodash/uniq';
import * as React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {PartitionDefinitionType, RepositorySelector} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {SortButton} from '../launchpad/ConfigEditorConfigPicker';
import {DimensionRangeWizard} from '../partitions/DimensionRangeWizard';
import {testId} from '../testing/testId';

import {AssetPartitionDetailEmpty, AssetPartitionDetailLoader} from './AssetPartitionDetail';
import {AssetPartitionList} from './AssetPartitionList';
import {AssetPartitionStatus} from './AssetPartitionStatus';
import {AssetPartitionStatusCheckboxes} from './AssetPartitionStatusCheckboxes';
import {AssetViewParams} from './AssetView';
import {isTimeseriesDimension} from './MultipartitioningSupport';
import {AssetKey} from './types';
import {usePartitionDimensionSelections} from './usePartitionDimensionSelections';
import {
  usePartitionHealthData,
  rangesClippedToSelection,
  keyCountByStateInSelection,
  partitionStatusAtIndex,
  selectionRangeWithSingleKey,
} from './usePartitionHealthData';
import {usePartitionKeyInParams} from './usePartitionKeyInParams';

interface Props {
  assetKey: AssetKey;
  assetPartitionDimensions?: string[];
  liveData?: LiveDataForNode;
  params: AssetViewParams;
  paramsTimeWindowOnly: boolean;
  setParams: (params: AssetViewParams) => void;

  // This timestamp is a "hint", when it changes this component will refetch
  // to retrieve new data. Just don't want to poll the entire table query.
  dataRefreshHint: string | undefined;

  repository?: RepositorySelector;
  opName?: string | null;
}

const DISPLAYED_STATUSES = [
  AssetPartitionStatus.MISSING,
  AssetPartitionStatus.MATERIALIZING,
  AssetPartitionStatus.MATERIALIZED,
  AssetPartitionStatus.FAILED,
].sort();

export const AssetPartitions: React.FC<Props> = ({
  assetKey,
  assetPartitionDimensions,
  params,
  setParams,
  dataRefreshHint,
}) => {
  const [assetHealth] = usePartitionHealthData([assetKey], dataRefreshHint);
  const [selections, setSelections] = usePartitionDimensionSelections({
    knownDimensionNames: assetPartitionDimensions,
    modifyQueryString: true,
    assetHealth,
    shouldReadPartitionQueryStringParam: false,
  });

  const [selectionSorts, setSelectionSorts] = React.useState<Array<-1 | 1>>([]); // +1 for default sort, -1 for reverse sort

  const [statusFilters, setStatusFilters] = useQueryPersistedState<AssetPartitionStatus[]>({
    defaults: {status: [...DISPLAYED_STATUSES].sort().join(',')},
    encode: (val) => ({status: [...val].sort().join(',')}),
    decode: (qs) =>
      (qs.status || '')
        .split(',')
        .filter((s: AssetPartitionStatus) => DISPLAYED_STATUSES.includes(s)),
  });

  // Determine which axis we will show at the top of the page, if any.
  const timeDimensionIdx = selections.findIndex((s) => isTimeseriesDimension(s.dimension));

  const [focusedDimensionKeys, setFocusedDimensionKey] = usePartitionKeyInParams({
    params,
    setParams,
    dimensionCount: selections.length,
    defaultKeyInDimension: (dimensionIdx) => dimensionKeysInSelection(dimensionIdx)[0],
  });

  // Get asset health on all dimensions, with the non-time dimensions scoped
  // to the time dimension selection (so the status of partition "VA" reflects
  // the selection you've made on the time axis.)
  const rangesForEachDimension = React.useMemo(() => {
    if (!assetHealth) {
      return selections.map(() => []);
    }
    return selections.map((_s, idx) =>
      assetHealth.rangesForSingleDimension(
        idx,
        idx === 1 && focusedDimensionKeys[0]
          ? [selectionRangeWithSingleKey(focusedDimensionKeys[0], selections[0].dimension)]
          : timeDimensionIdx !== -1 && idx !== timeDimensionIdx
          ? selections[timeDimensionIdx].selectedRanges
          : undefined,
      ),
    );
  }, [assetHealth, selections, timeDimensionIdx, focusedDimensionKeys]);

  // This function returns the list of dimension keys INSIDE the `selections.selectedRanges`
  // specified at the top of the page that MATCH the state filters (success / completed).
  // There are pieces of this that could be moved to shared helpers, but we may discourage
  // loading the full key space and shift responsibility for this to GraphQL in the future.
  //
  const dimensionKeysInSelection = (idx: number) => {
    if (!selections[idx]) {
      return []; // loading
    }
    // Special case: If you have cleared the time selection in the top bar, we
    // clear all dimension columns, (even though you still have a dimension 2 selection)
    if (timeDimensionIdx !== -1 && selections[timeDimensionIdx].selectedRanges.length === 0) {
      return [];
    }

    const {dimension, selectedRanges} = selections[idx];
    const allKeys = dimension.partitionKeys;
    const sort = selectionSorts[idx] || defaultSort(selections[idx].dimension.type);

    const getSelectionKeys = () =>
      uniq(selectedRanges.flatMap(({start, end}) => allKeys.slice(start.idx, end.idx + 1)));

    if (isEqual(DISPLAYED_STATUSES, statusFilters)) {
      const result = getSelectionKeys();
      return sort === 1 ? result : result.reverse();
    }

    const healthRangesInSelection = rangesClippedToSelection(
      rangesForEachDimension[idx],
      selectedRanges,
    );
    const getKeysWithStates = (states: AssetPartitionStatus[]) => {
      return healthRangesInSelection.flatMap((r) =>
        states.some((s) => r.value.includes(s)) ? allKeys.slice(r.start.idx, r.end.idx + 1) : [],
      );
    };

    const matching = uniq(
      getKeysWithStates(statusFilters.filter((f) => f !== AssetPartitionStatus.MISSING)),
    );

    let result;
    // We have to add in "missing" separately because it's the absence of a range
    if (statusFilters.includes(AssetPartitionStatus.MISSING)) {
      const selectionKeys = getSelectionKeys();
      const isMissingForIndex = (idx: number) =>
        !healthRangesInSelection.some(
          (r) =>
            r.start.idx <= idx &&
            r.end.idx >= idx &&
            !r.value.includes(AssetPartitionStatus.MISSING),
        );
      result = allKeys.filter(
        (a, pidx) => selectionKeys.includes(a) && (matching.includes(a) || isMissingForIndex(pidx)),
      );
    } else {
      result = matching;
    }

    return sort === 1 ? result : result.reverse();
  };

  const countsByStateInSelection = keyCountByStateInSelection(assetHealth, selections);
  const countsFiltered = statusFilters.reduce((a, b) => a + countsByStateInSelection[b], 0);

  return (
    <>
      {timeDimensionIdx !== -1 && (
        <Box
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <DimensionRangeWizard
            partitionKeys={selections[timeDimensionIdx].dimension.partitionKeys}
            health={{ranges: rangesForEachDimension[timeDimensionIdx]}}
            selected={selections[timeDimensionIdx].selectedKeys}
            setSelected={(selectedKeys) =>
              setSelections(
                selections.map((r, idx) => (idx === timeDimensionIdx ? {...r, selectedKeys} : r)),
              )
            }
            dimensionType={selections[timeDimensionIdx].dimension.type}
          />
        </Box>
      )}

      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', justifyContent: 'space-between'}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <div data-testid={testId('partitions-selected')}>
          {countsFiltered.toLocaleString()} Partitions Selected
        </div>
        <AssetPartitionStatusCheckboxes
          counts={countsByStateInSelection}
          allowed={DISPLAYED_STATUSES}
          value={statusFilters}
          onChange={setStatusFilters}
        />
      </Box>
      <Box style={{flex: 1, minHeight: 0, outline: 'none'}} flex={{direction: 'row'}} tabIndex={-1}>
        {selections.map((selection, idx) => (
          <Box
            key={selection.dimension.name}
            style={{display: 'flex', flex: 1, paddingRight: 1, minWidth: 200}}
            flex={{direction: 'column'}}
            border={{side: 'right', color: Colors.KeylineGray, width: 1}}
            background={Colors.Gray50}
            data-testid={testId(`partitions-${selection.dimension.name}`)}
          >
            <Box
              flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
              background={Colors.White}
              border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
              padding={{horizontal: 24, vertical: 8}}
            >
              <div>
                {selection.dimension.name !== 'default' && (
                  <Box flex={{gap: 8, alignItems: 'center'}}>
                    <Icon name="partition" />
                    <Subheading>{selection.dimension.name}</Subheading>
                  </Box>
                )}
              </div>
              <SortButton
                style={{marginRight: '-16px'}}
                data-testid={`sort-${idx}`}
                onClick={() => {
                  setSelectionSorts((sorts) => {
                    const copy = [...sorts];
                    if (copy[idx]) {
                      copy[idx] = copy[idx] === -1 ? 1 : -1;
                    } else {
                      copy[idx] = (defaultSort(selections[idx].dimension.type) * -1) as -1 | 1;
                    }
                    return copy;
                  });
                }}
              >
                <Icon name="sort_by_alpha" color={Colors.Gray400} />
              </SortButton>
            </Box>

            {!assetHealth ? (
              <Box flex={{alignItems: 'center', justifyContent: 'center'}} style={{flex: 1}}>
                <Spinner purpose="section" />
              </Box>
            ) : (
              <AssetPartitionList
                partitions={dimensionKeysInSelection(idx)}
                statusForPartition={(dimensionKey) => {
                  if (idx === 1 && focusedDimensionKeys[0]) {
                    return [assetHealth.stateForKey([focusedDimensionKeys[0], dimensionKey])];
                  }
                  const dimensionKeyIdx = selection.dimension.partitionKeys.indexOf(dimensionKey);
                  return partitionStatusAtIndex(
                    rangesForEachDimension[idx],
                    dimensionKeyIdx,
                  ).filter((s) => statusFilters.includes(s));
                }}
                focusedDimensionKey={focusedDimensionKeys[idx]}
                setFocusedDimensionKey={(dimensionKey) => {
                  setFocusedDimensionKey(idx, dimensionKey);
                }}
              />
            )}
          </Box>
        ))}

        <Box style={{flex: 3, minWidth: 0, overflowY: 'auto'}} flex={{direction: 'column'}}>
          {params.partition && focusedDimensionKeys.length === selections.length ? (
            <AssetPartitionDetailLoader assetKey={assetKey} partitionKey={params.partition} />
          ) : (
            <AssetPartitionDetailEmpty />
          )}
        </Box>
      </Box>
    </>
  );
};

function defaultSort(definitionType: PartitionDefinitionType) {
  if (definitionType === PartitionDefinitionType.TIME_WINDOW) {
    return -1;
  } else {
    return 1;
  }
}
