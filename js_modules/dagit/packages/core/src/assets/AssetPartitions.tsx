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
  keyCountInSelection,
  keyCountInRanges,
} from './usePartitionHealthData';

interface Props {
  assetKey: AssetKey;
  assetPartitionDimensions?: string[];
  liveData?: LiveDataForNode;
  params: AssetViewParams;
  paramsTimeWindowOnly: boolean;
  setParams: (params: AssetViewParams) => void;

  // This timestamp is a "hint", when it changes this component will refetch
  // to retrieve new data. Just don't want to poll the entire table query.
  assetLastMaterializedAt: string | undefined;

  repository?: RepositorySelector;
  opName?: string | null;
}

const DISPLAYED_STATES = [PartitionState.MISSING, PartitionState.SUCCESS];

export const AssetPartitions: React.FC<Props> = ({
  assetKey,
  assetPartitionDimensions,
  assetLastMaterializedAt,
  params,
  setParams,
  liveData,
}) => {
  const [assetHealth] = usePartitionHealthData([assetKey], assetLastMaterializedAt);
  const [selections, setSelections] = usePartitionDimensionSelections({
    knownDimensionNames: assetPartitionDimensions,
    modifyQueryString: true,
    assetHealth,
  });

  const [stateFilters, setStateFilters] = useQueryPersistedState<PartitionState[]>({
    defaults: {states: [...DISPLAYED_STATES].sort().join(',')},
    encode: (val) => ({states: [...val].sort().join(',')}),
    decode: (qs) =>
      (qs.states || '').split(',').filter((s: PartitionState) => DISPLAYED_STATES.includes(s)),
  });

  const timeDimensionIdx = selections.findIndex((s) => isTimeseriesDimension(s.dimension));
  const timeDimension = timeDimensionIdx !== -1 ? assetHealth.dimensions[timeDimensionIdx] : null;

  const focusedDimensionKeys = params.partition
    ? selections.length > 1
      ? params.partition.split('|').filter(Boolean)
      : [params.partition] // "|" character is allowed in 1D partition keys for historical reasons
    : [];

  const ranges = selections.map((_s, idx) =>
    assetHealth
      ? assetHealth.rangesForSingleDimension(
          idx,
          timeDimensionIdx !== -1 && idx !== timeDimensionIdx
            ? selections[timeDimensionIdx].selectedRanges
            : undefined,
        )
      : [],
  );

  const dimensionKeysInSelection = (idx: number) => {
    const {dimension, selectedRanges} = selections[idx];
    const allKeys = dimension.partitionKeys;

    const getSelectionKeys = () =>
      uniq(selectedRanges.flatMap(([start, end]) => allKeys.slice(start.idx, end.idx + 1)));

    const getSuccessKeys = () => {
      const materializedInSelection = rangesClippedToSelection(ranges[idx], selectedRanges);
      return materializedInSelection.flatMap((r) => allKeys.slice(r.start.idx, r.end.idx + 1));
    };

    if (isEqual(DISPLAYED_STATES, stateFilters)) {
      return getSelectionKeys();
    } else if (isEqual([PartitionState.SUCCESS], stateFilters)) {
      return uniq(getSuccessKeys());
    } else if (isEqual([PartitionState.MISSING], stateFilters)) {
      return without(getSelectionKeys(), ...getSuccessKeys());
    } else {
      return [];
    }
  };

  const countsByStateInSelection = (() => {
    const total = selections
      .map((s) => keyCountInSelection(s.selectedRanges))
      .reduce((a, b) => (a ? a * b : b), 0);

    const rangesInSelection = rangesClippedToSelection(ranges[0], selections[0].selectedRanges);
    const success = rangesInSelection.reduce(
      (a, b) =>
        a + (b.end.idx - b.start.idx + 1) * (b.subranges ? keyCountInRanges(b.subranges) : 1),
      0,
    );

    return {
      [PartitionState.MISSING]: total - success,
      [PartitionState.SUCCESS]: success,
    };
  })();

  const countsFiltered = stateFilters.reduce((a, b) => a + countsByStateInSelection[b], 0);

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
      {timeDimension && (
        <Box
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <DimensionRangeWizard
            partitionKeys={timeDimension.partitionKeys}
            health={{ranges: ranges[timeDimensionIdx]}}
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
        <div>{countsFiltered.toLocaleString()} Partitions Selected</div>
        <PartitionStateCheckboxes
          counts={countsByStateInSelection}
          allowed={[PartitionState.MISSING, PartitionState.SUCCESS]}
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
                  const dimensionIdx = selection.dimension.partitionKeys.indexOf(dimensionKey);
                  return (
                    ranges[idx].find(
                      (r) => r.start.idx <= dimensionIdx && r.end.idx >= dimensionIdx,
                    )?.value || PartitionState.MISSING
                  );
                }}
                focusedDimensionKey={focusedDimensionKeys[idx]}
                setFocusedDimensionKey={(dimensionKey) => {
                  const nextFocusedDimensionKeys: string[] = [];
                  for (let ii = 0; ii < idx; ii++) {
                    nextFocusedDimensionKeys.push(
                      focusedDimensionKeys[ii] || dimensionKeysInSelection[0],
                    );
                  }
                  if (dimensionKey) {
                    nextFocusedDimensionKeys.push(dimensionKey);
                  }
                  setParams({
                    ...params,
                    partition: nextFocusedDimensionKeys.join('|'),
                  });
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
