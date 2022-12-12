import {Box, Colors, Icon, Spinner, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {PartitionRangeWizard} from '../partitions/PartitionRangeWizard';
import {PartitionStateCheckboxes} from '../partitions/PartitionStateCheckboxes';
import {PartitionState} from '../partitions/PartitionStatus';
import {RepositorySelector} from '../types/globalTypes';

import {AssetPartitionDetailEmpty, AssetPartitionDetailLoader} from './AssetPartitionDetail';
import {AssetPartitionList} from './AssetPartitionList';
import {AssetViewParams} from './AssetView';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunsSinceMaterializationBanner} from './FailedRunsSinceMaterializationBanner';
import {explodePartitionKeysInRanges, isTimeseriesDimension} from './MultipartitioningSupport';
import {AssetKey} from './types';
import {usePartitionDimensionRanges} from './usePartitionDimensionRanges';
import {PartitionHealthDimensionRange, usePartitionHealthData} from './usePartitionHealthData';

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
  const [ranges, setRanges] = usePartitionDimensionRanges(
    assetHealth,
    assetPartitionDimensions,
    true,
  );

  const [stateFilters, setStateFilters] = useQueryPersistedState<PartitionState[]>({
    defaults: {states: DISPLAYED_STATES.sort().join(',')},
    encode: (val) => ({states: [...val].sort().join(',')}),
    decode: (qs) =>
      (qs.states || '').split(',').filter((s: PartitionState) => DISPLAYED_STATES.includes(s)),
  });

  const timeRangeIdx = ranges.findIndex((r) => isTimeseriesDimension(r.dimension));
  const timeRange = timeRangeIdx !== -1 ? ranges[timeRangeIdx] : null;

  const allInRanges = React.useMemo(() => {
    return assetHealth ? explodePartitionKeysInRanges(ranges, assetHealth.stateForKey) : [];
  }, [ranges, assetHealth]);

  const allSelected = React.useMemo(
    () => allInRanges.filter((p) => stateFilters.includes(p.state)),
    [allInRanges, stateFilters],
  );

  const focusedDimensionKeys = params.partition
    ? ranges.length > 1
      ? params.partition.split('|').filter(Boolean)
      : [params.partition] // "|" character is allowed in 1D partition keys for historical reasons
    : [];

  const dimensionKeysOrdered = (range: PartitionHealthDimensionRange) => {
    return isTimeseriesDimension(range.dimension) ? [...range.selected].reverse() : range.selected;
  };
  const dimensionRowsForRange = (range: PartitionHealthDimensionRange, idx: number) => {
    if (timeRange && timeRange.selected.length === 0) {
      return [];
    }
    return dimensionKeysOrdered(range)
      .map((dimensionKey) => {
        // Note: If you have clicked dimension 1, dimension 2 shows the state of each subkey. If
        // you have not clicked dimension 1, dimension 2 shows the merged state of all the keys
        // in that dimension (for all values of dimension 1)
        const state =
          idx > 0 && focusedDimensionKeys.length >= idx
            ? assetHealth.stateForPartialKey([...focusedDimensionKeys.slice(0, idx), dimensionKey])
            : assetHealth.stateForSingleDimension(
                idx,
                dimensionKey,
                range !== timeRange ? timeRange?.selected : undefined,
              );

        return {dimensionKey, state};
      })
      .filter(
        (row) =>
          stateFilters.includes(row.state) ||
          (row.state === PartitionState.SUCCESS_MISSING &&
            (stateFilters.includes(PartitionState.SUCCESS) ||
              stateFilters.includes(PartitionState.MISSING))),
      );
  };

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
      {timeRange && (
        <Box
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <PartitionRangeWizard
            partitionKeys={timeRange.dimension.partitionKeys}
            partitionStateForKey={(dimensionKey) =>
              assetHealth.stateForSingleDimension(timeRangeIdx, dimensionKey)
            }
            selected={timeRange.selected}
            setSelected={(selected) =>
              setRanges(ranges.map((r) => (r === timeRange ? {...r, selected} : r)))
            }
          />
        </Box>
      )}

      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', justifyContent: 'space-between'}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <div>{allSelected.length.toLocaleString()} Partitions Selected</div>
        <PartitionStateCheckboxes
          partitionKeysForCounts={allInRanges}
          allowed={[PartitionState.MISSING, PartitionState.SUCCESS]}
          value={stateFilters}
          onChange={setStateFilters}
        />
      </Box>
      <Box style={{flex: 1, minHeight: 0, outline: 'none'}} flex={{direction: 'row'}} tabIndex={-1}>
        {ranges.map((range, idx) => (
          <Box
            key={range.dimension.name}
            style={{display: 'flex', flex: 1, paddingRight: 1, minWidth: 200}}
            flex={{direction: 'column'}}
            border={{side: 'right', color: Colors.KeylineGray, width: 1}}
            background={Colors.Gray50}
          >
            {range.dimension.name !== 'default' && (
              <Box
                padding={{horizontal: 24, vertical: 8}}
                flex={{gap: 8, alignItems: 'center'}}
                background={Colors.White}
                border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
              >
                <Icon name="partition" />
                <Subheading>{range.dimension.name}</Subheading>
              </Box>
            )}

            {!assetHealth ? (
              <Box flex={{alignItems: 'center', justifyContent: 'center'}} style={{flex: 1}}>
                <Spinner purpose="section" />
              </Box>
            ) : (
              <AssetPartitionList
                partitions={dimensionRowsForRange(range, idx)}
                focusedDimensionKey={focusedDimensionKeys[idx]}
                setFocusedDimensionKey={(dimensionKey) => {
                  const nextFocusedDimensionKeys: string[] = [];
                  for (let ii = 0; ii < idx; ii++) {
                    nextFocusedDimensionKeys.push(
                      focusedDimensionKeys[ii] || dimensionKeysOrdered(ranges[ii])[0],
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

        <Box style={{flex: 3, minWidth: 0}} flex={{direction: 'column'}}>
          {params.partition && focusedDimensionKeys.length === ranges.length ? (
            <AssetPartitionDetailLoader assetKey={assetKey} partitionKey={params.partition} />
          ) : (
            <AssetPartitionDetailEmpty />
          )}
        </Box>
      </Box>
    </>
  );
};
