import {Box, Colors, Icon, Spinner, Subheading} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import uniq from 'lodash/uniq';
import without from 'lodash/without';
import * as React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {RepositorySelector} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {DimensionRangeWizard} from '../partitions/DimensionRangeWizard';
import {PartitionStateCheckboxes} from '../partitions/PartitionStateCheckboxes';
import {PartitionState} from '../partitions/PartitionStatus';
import {testId} from '../testing/testId';

import {AssetPartitionDetailEmpty, AssetPartitionDetailLoader} from './AssetPartitionDetail';
import {AssetPartitionList} from './AssetPartitionList';
import {AssetViewParams} from './AssetView';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunsSinceMaterializationBanner} from './FailedRunsSinceMaterializationBanner';
import {isTimeseriesDimension} from './MultipartitioningSupport';
import {AssetKey} from './types';
import {usePartitionDimensionSelections} from './usePartitionDimensionSelections';
import {
  usePartitionHealthData,
  rangesClippedToSelection,
  keyCountByStateInSelection,
  partitionStateAtIndex,
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

const DISPLAYED_STATES = [PartitionState.MISSING, PartitionState.SUCCESS, PartitionState.FAILURE];

export const AssetPartitions: React.FC<Props> = ({
  assetKey,
  assetPartitionDimensions,
  params,
  setParams,
  liveData,
  dataRefreshHint,
}) => {
  const [assetHealth] = usePartitionHealthData([assetKey], dataRefreshHint);
  const [selections, setSelections] = usePartitionDimensionSelections({
    knownDimensionNames: assetPartitionDimensions,
    modifyQueryString: true,
    assetHealth,
    shouldReadPartitionQueryStringParam: false,
  });

  const [stateFilters, setStateFilters] = useQueryPersistedState<PartitionState[]>({
    defaults: {states: [...DISPLAYED_STATES].sort().join(',')},
    encode: (val) => ({states: [...val].sort().join(',')}),
    decode: (qs) =>
      (qs.states || '').split(',').filter((s: PartitionState) => DISPLAYED_STATES.includes(s)),
  });

  // Determine which axis we will show at the top of the page, if any.
  const timeDimensionIdx = selections.findIndex((s) => isTimeseriesDimension(s.dimension));

  // Get asset health on all dimensions, with the non-time dimensions scoped
  // to the time dimension selection (so the status of partition "VA" reflects
  // the selection you've made on the time axis.)
  const materializedRangesByDimension = React.useMemo(
    () =>
      selections.map((_s, idx) =>
        assetHealth
          ? assetHealth.rangesForSingleDimension(
              idx,
              timeDimensionIdx !== -1 && idx !== timeDimensionIdx
                ? selections[timeDimensionIdx].selectedRanges
                : undefined,
            )
          : [],
      ),
    [assetHealth, selections, timeDimensionIdx],
  );

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

    const getSelectionKeys = () =>
      uniq(selectedRanges.flatMap(([start, end]) => allKeys.slice(start.idx, end.idx + 1)));

    const getKeysWithStates = (states: PartitionState[]) => {
      const materializedInSelection = rangesClippedToSelection(
        materializedRangesByDimension[idx],
        selectedRanges,
      );
      return materializedInSelection.flatMap((r) =>
        states.includes(r.value) ? allKeys.slice(r.start.idx, r.end.idx + 1) : [],
      );
    };

    if (isEqual(DISPLAYED_STATES, stateFilters)) {
      return getSelectionKeys(); // optimization for the default case
    }

    const states: PartitionState[] = [];
    if (stateFilters.includes(PartitionState.SUCCESS)) {
      states.push(PartitionState.SUCCESS, PartitionState.SUCCESS_MISSING);
    }
    if (stateFilters.includes(PartitionState.FAILURE)) {
      states.push(PartitionState.FAILURE);
    }
    const matching = uniq(getKeysWithStates(states));

    // We have to add in "missing" separately because it's the absence of a range
    if (stateFilters.includes(PartitionState.MISSING)) {
      const missing = without(
        getSelectionKeys(),
        ...getKeysWithStates([PartitionState.SUCCESS, PartitionState.FAILURE]),
      );
      return uniq([...matching, ...missing]);
    } else {
      return matching;
    }
  };

  const countsByStateInSelection = keyCountByStateInSelection(assetHealth, selections);
  const countsFiltered = stateFilters.reduce((a, b) => a + countsByStateInSelection[b], 0);

  const [focusedDimensionKeys, setFocusedDimensionKey] = usePartitionKeyInParams({
    params,
    setParams,
    dimensionCount: selections.length,
    defaultKeyInDimension: (dimensionIdx) => dimensionKeysInSelection(dimensionIdx)[0],
  });

  return (
    <>
      <FailedRunsSinceMaterializationBanner
        liveData={liveData}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      />

      <CurrentRunsBanner
        liveData={liveData}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      />
      {timeDimensionIdx !== -1 && (
        <Box
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <DimensionRangeWizard
            partitionKeys={selections[timeDimensionIdx].dimension.partitionKeys}
            health={{ranges: materializedRangesByDimension[timeDimensionIdx]}}
            selected={selections[timeDimensionIdx].selectedKeys}
            setSelected={(selectedKeys) =>
              setSelections(
                selections.map((r, idx) => (idx === timeDimensionIdx ? {...r, selectedKeys} : r)),
              )
            }
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
        <PartitionStateCheckboxes
          counts={countsByStateInSelection}
          allowed={[PartitionState.MISSING, PartitionState.SUCCESS, PartitionState.FAILURE]}
          value={stateFilters}
          onChange={setStateFilters}
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
          >
            {selection.dimension.name !== 'default' && (
              <Box
                padding={{horizontal: 24, vertical: 8}}
                flex={{gap: 8, alignItems: 'center'}}
                background={Colors.White}
                border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
              >
                <Icon name="partition" />
                <Subheading>{selection.dimension.name}</Subheading>
              </Box>
            )}

            {!assetHealth ? (
              <Box flex={{alignItems: 'center', justifyContent: 'center'}} style={{flex: 1}}>
                <Spinner purpose="section" />
              </Box>
            ) : (
              <AssetPartitionList
                partitions={dimensionKeysInSelection(idx)}
                stateForPartition={(dimensionKey) => {
                  if (idx === 1 && focusedDimensionKeys[0]) {
                    return assetHealth.stateForKey([focusedDimensionKeys[0], dimensionKey]);
                  }
                  const dimensionKeyIdx = selection.dimension.partitionKeys.indexOf(dimensionKey);
                  return partitionStateAtIndex(materializedRangesByDimension[idx], dimensionKeyIdx);
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
