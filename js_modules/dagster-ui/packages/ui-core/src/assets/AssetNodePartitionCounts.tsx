import {Box, Colors, Icon, IconName, Tooltip} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {LiveDataForNode} from '../asset-graph/Utils';
import {AssetNodeFragment} from '../asset-graph/types/AssetNode.types';
import {AssetPartitionStatus} from '../assets/AssetPartitionStatus';

export const partitionCountString = (count: number | undefined, adjective = '') =>
  `${count === undefined ? '-' : count.toLocaleString()} ${adjective}${adjective ? ' ' : ''}${
    count === 1 ? 'partition' : 'partitions'
  }`;

const countMissing = (partitionStats: LiveDataForNode['partitionStats'] | null | undefined) =>
  partitionStats
    ? partitionStats.numPartitions -
      partitionStats.numFailed -
      partitionStats.numMaterializing -
      partitionStats.numMaterialized
    : undefined;

export const StyleForAssetPartitionStatus: Record<
  AssetPartitionStatus,
  {
    background: string;
    foreground: string;
    border: string;
    icon: IconName;
    adjective: string;
  }
> = {
  [AssetPartitionStatus.FAILED]: {
    background: Colors.backgroundRed(),
    foreground: Colors.textRed(),
    border: Colors.accentRed(),
    icon: 'partition_failure',
    adjective: 'failed',
  },
  [AssetPartitionStatus.MATERIALIZED]: {
    background: Colors.backgroundGreen(),
    foreground: Colors.textGreen(),
    border: Colors.accentGreen(),
    icon: 'partition_success',
    adjective: 'materialized',
  },
  [AssetPartitionStatus.MATERIALIZING]: {
    background: Colors.backgroundBlue(),
    foreground: Colors.textBlue(),
    border: Colors.accentBlue(),
    icon: 'partition_success',
    adjective: 'materializing',
  },
  [AssetPartitionStatus.MISSING]: {
    background: Colors.backgroundGray(),
    foreground: Colors.textLight(),
    border: Colors.accentGray(),
    icon: 'partition_missing',
    adjective: 'missing',
  },
};

export const PartitionCountTags = (props: {
  definition: AssetNodeFragment;
  liveData: LiveDataForNode | undefined;
}) => {
  const data = props.liveData?.partitionStats;
  return (
    <Box style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 2}}>
      <PartitionCountTag
        status={AssetPartitionStatus.MATERIALIZED}
        value={data?.numMaterialized}
        total={data?.numPartitions}
      />
      <PartitionCountTag
        status={AssetPartitionStatus.MISSING}
        value={countMissing(data)}
        total={data?.numPartitions}
      />
      <PartitionCountTag
        status={AssetPartitionStatus.FAILED}
        value={data?.numFailed}
        total={data?.numPartitions}
      />
    </Box>
  );
};

const PartitionCountTag = ({
  status,
  value,
  total,
}: {
  status: AssetPartitionStatus;
  value: number | undefined;
  total: number | undefined;
}) => {
  const style = StyleForAssetPartitionStatus[status];
  const foreground = value ? style.foreground : Colors.textLight();
  const background = value ? style.background : Colors.backgroundGray();

  return (
    <Tooltip
      display="block"
      position="top"
      canShow={value !== undefined}
      content={partitionCountString(value, style.adjective)}
    >
      <PartitionCountContainer style={{color: foreground, background}}>
        <Icon name={style.icon} color={foreground} size={12} />
        {value === undefined ? '—' : value === total ? 'All' : value > 1000 ? '999+' : value}
      </PartitionCountContainer>
    </Tooltip>
  );
};

export const PartitionCountLabels = ({
  partitionStats,
}: {
  partitionStats: LiveDataForNode['partitionStats'] | null | undefined;
}) => {
  return (
    <Box style={{display: 'flex', gap: 8}}>
      <PartitionCountLabel
        status={AssetPartitionStatus.MATERIALIZED}
        value={partitionStats?.numMaterialized}
        total={partitionStats?.numPartitions}
      />
      <PartitionCountLabel
        status={AssetPartitionStatus.MISSING}
        value={countMissing(partitionStats)}
        total={partitionStats?.numPartitions}
      />
      <PartitionCountLabel
        status={AssetPartitionStatus.FAILED}
        value={partitionStats?.numFailed}
        total={partitionStats?.numPartitions}
      />
      <PartitionCountLabel
        status={AssetPartitionStatus.MATERIALIZING}
        value={partitionStats?.numMaterializing}
        total={partitionStats?.numPartitions}
      />
    </Box>
  );
};

const PartitionCountLabel = ({
  status,
  value,
  total,
}: {
  status: AssetPartitionStatus;
  value: number | undefined;
  total: number | undefined;
}) => {
  const style = StyleForAssetPartitionStatus[status];

  return (
    <Tooltip
      display="block"
      position="top"
      canShow={value !== undefined}
      content={partitionCountString(value, style.adjective)}
    >
      <Box
        flex={{gap: 4, alignItems: 'center'}}
        style={{
          color: value === undefined || value === 0 ? Colors.textLighter() : Colors.textDefault(),
        }}
      >
        <Icon name={style.icon} color={value ? style.border : Colors.textLighter()} size={12} />
        {value === undefined ? '—' : value === total ? 'All' : value.toLocaleString()}
      </Box>
    </Tooltip>
  );
};

// Necessary to remove the outline we get with the tooltip applying a tabIndex
const PartitionCountContainer = styled.div`
  width: 100%;
  border-radius: 6px;
  font-size: 12px;
  gap: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
`;
