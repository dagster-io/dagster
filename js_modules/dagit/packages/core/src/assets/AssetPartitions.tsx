import {Box, Colors, Icon, Spinner, Subheading} from '@dagster-io/ui';
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
import {explodePartitionKeysInSelection, isTimeseriesDimension} from './MultipartitioningSupport';
import {AssetKey} from './types';
import {usePartitionDimensionSelections} from './usePartitionDimensionSelections';
import {PartitionDimensionSelection, usePartitionHealthData} from './usePartitionHealthData';

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
  const [ranges, setRanges] = usePartitionDimensionSelections({
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

  const timeRangeIdx = ranges.findIndex((r) => isTimeseriesDimension(r.dimension));
  const timeRange = timeRangeIdx !== -1 ? ranges[timeRangeIdx] : null;

  const keysInSelection = React.useMemo(() => {
    return assetHealth ? explodePartitionKeysInSelection(ranges, assetHealth.stateForKey) : [];
  }, [ranges, assetHealth]);

  const keysFiltered = React.useMemo(
    () => keysInSelection.filter((p) => stateFilters.includes(p.state)),
    [keysInSelection, stateFilters],
  );

  const focusedDimensionKeys = params.partition
    ? ranges.length > 1
      ? params.partition.split('|').filter(Boolean)
      : [params.partition] // "|" character is allowed in 1D partition keys for historical reasons
    : [];

  const dimensionKeysOrdered = (range: PartitionDimensionSelection) => {
    return isTimeseriesDimension(range.dimension)
      ? [...range.selectedKeys].reverse()
      : range.selectedKeys;
  };
  const dimensionRowsForRange = (range: PartitionDimensionSelection, idx: number) => {
    if (timeRange && timeRange.selectedKeys.length === 0) {
      return [];
    }
    return dimensionKeysOrdered(range)
      .map((dimensionKey) => {
        // Note: If you have clicked dimension 1, dimension 2 shows the state of each subkey. If
        // you have not clicked dimension 1, dimension 2 shows the merged state of all the keys
        // in that dimension (for all values of dimension 1)
        const state =
          idx === 1 && focusedDimensionKeys.length >= 1
            ? assetHealth.stateForKey([focusedDimensionKeys[0], dimensionKey])
            : assetHealth.stateForSingleDimension(
                idx,
                dimensionKey,
                range !== timeRange ? timeRange?.selectedKeys : undefined,
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
          <DimensionRangeWizard
            partitionKeys={timeRange.dimension.partitionKeys}
            partitionStateForKey={(dimensionKey) =>
              assetHealth.stateForSingleDimension(timeRangeIdx, dimensionKey)
            }
            selected={timeRange.selectedKeys}
            setSelected={(selectedKeys) =>
              setRanges(ranges.map((r) => (r === timeRange ? {...r, selectedKeys} : r)))
            }
          />
        </Box>
      )}

      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', justifyContent: 'space-between'}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <div>{keysFiltered.length.toLocaleString()} Partitions Selected</div>
        <PartitionStateCheckboxes
          partitionKeysForCounts={keysInSelection}
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

        <Box style={{flex: 3, minWidth: 0, overflowY: 'auto'}} flex={{direction: 'column'}}>
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
