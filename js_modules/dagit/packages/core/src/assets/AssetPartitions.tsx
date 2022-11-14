import {Box, Colors, Spinner} from '@dagster-io/ui';
import * as React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {PartitionRangeWizard} from '../partitions/PartitionRangeWizard';
import {PartitionStateCheckboxes} from '../partitions/PartitionStateCheckboxes';
import {PartitionState} from '../partitions/PartitionStatus';
import {RepositorySelector} from '../types/globalTypes';

import {AssetPartitionDetailEmpty, AssetPartitionDetailLoader} from './AssetPartitionDetail';
import {AssetPartitionList} from './AssetPartitionList';
import {AssetViewParams} from './AssetView';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunsSinceMaterializationBanner} from './FailedRunsSinceMaterializationBanner';
import {assetHealthToPartitionStatus} from './LaunchAssetChoosePartitionsDialog';
import {usePartitionHealthData} from './PartitionHealthSummary';
import {AssetKey} from './types';

interface Props {
  assetKey: AssetKey;
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

export const AssetPartitions: React.FC<Props> = ({assetKey, params, setParams, liveData}) => {
  const [assetHealth] = usePartitionHealthData([assetKey]);
  const partitionNames = React.useMemo(() => assetHealth?.keys || [], [assetHealth]);
  const partitionStatusData = React.useMemo(() => assetHealthToPartitionStatus([assetHealth]), [
    assetHealth,
  ]);

  const [rangePartitionKeys, setRangePartitionKeys] = React.useState<string[]>([]);
  const [stateFilters, setStateFilters] = React.useState<PartitionState[]>([
    PartitionState.MISSING,
    PartitionState.SUCCESS,
  ]);

  React.useEffect(() => {
    setRangePartitionKeys(partitionNames);
  }, [partitionNames]);

  const selectedPartitionKeys = React.useMemo(() => {
    return rangePartitionKeys.filter((r) => stateFilters.includes(partitionStatusData[r]));
  }, [rangePartitionKeys, stateFilters, partitionStatusData]);

  const onKeyDown = (e: React.KeyboardEvent<any>) => {
    const shift = {ArrowDown: 1, ArrowUp: -1}[e.key];
    if (!shift || !params.partition || e.isDefaultPrevented()) {
      return;
    }
    const next = selectedPartitionKeys[selectedPartitionKeys.indexOf(params.partition) + shift];
    if (next) {
      e.preventDefault();
      setParams({...params, partition: next});
    }
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
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <PartitionRangeWizard
          all={partitionNames}
          partitionData={partitionStatusData}
          selected={rangePartitionKeys}
          setSelected={setRangePartitionKeys}
        />
      </Box>

      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', justifyContent: 'space-between'}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <div>{selectedPartitionKeys.length.toLocaleString()} Partitions Selected</div>
        <PartitionStateCheckboxes
          allowed={[PartitionState.MISSING, PartitionState.SUCCESS]}
          value={stateFilters}
          onChange={setStateFilters}
          partitionData={partitionStatusData}
          partitionKeysForCounts={selectedPartitionKeys}
        />
      </Box>
      <Box
        style={{flex: 1, minHeight: 0, outline: 'none'}}
        flex={{direction: 'row'}}
        onKeyDown={onKeyDown}
        tabIndex={-1}
      >
        <Box
          style={{display: 'flex', flex: 1}}
          flex={{direction: 'column'}}
          background={Colors.Gray50}
        >
          {!assetHealth ? (
            <Box flex={{alignItems: 'center', justifyContent: 'center'}} style={{flex: 1}}>
              <Spinner purpose="section" />
            </Box>
          ) : (
            <AssetPartitionList
              partitionKeys={selectedPartitionKeys}
              partitionStatusData={partitionStatusData}
              focused={params.partition}
              setFocused={(partition) => setParams({...params, partition})}
            />
          )}
        </Box>

        <Box
          style={{flex: 3}}
          flex={{direction: 'column'}}
          border={{side: 'left', color: Colors.KeylineGray, width: 1}}
        >
          {params.partition ? (
            <AssetPartitionDetailLoader assetKey={assetKey} partitionKey={params.partition} />
          ) : (
            <AssetPartitionDetailEmpty />
          )}
        </Box>
      </Box>
    </>
  );
};
