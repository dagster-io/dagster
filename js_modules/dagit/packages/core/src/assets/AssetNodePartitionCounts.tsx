import {Colors, Icon, Box, Tooltip, IconName} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

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

export const StyleForAssetPartitionStatus: {
  [state: string]: {
    background: string;
    foreground: string;
    border: string;
    icon: IconName;
    adjective: string;
  };
} = {
  [AssetPartitionStatus.FAILED]: {
    background: Colors.Red50,
    foreground: Colors.Red700,
    border: Colors.Red500,
    icon: 'partition_failure',
    adjective: 'failed',
  },
  [AssetPartitionStatus.MATERIALIZED]: {
    background: Colors.Green50,
    foreground: Colors.Green700,
    border: Colors.Green500,
    icon: 'partition_success',
    adjective: 'materialized',
  },
  [AssetPartitionStatus.MATERIALIZING]: {
    background: Colors.Blue50,
    foreground: Colors.Blue700,
    border: Colors.Blue500,
    icon: 'partition_success',
    adjective: 'materializing',
  },
  [AssetPartitionStatus.MISSING]: {
    background: Colors.Gray100,
    foreground: Colors.Gray900,
    border: Colors.Gray500,
    icon: 'partition_missing',
    adjective: 'missing',
  },
};

export const PartitionCountTags: React.FC<{
  definition: AssetNodeFragment;
  liveData: LiveDataForNode | undefined;
}> = (props) => {
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

const PartitionCountTag: React.FC<{
  status: AssetPartitionStatus;
  value: number | undefined;
  total: number | undefined;
}> = ({status, value, total}) => {
  const style = StyleForAssetPartitionStatus[status];
  const foreground = value ? style.foreground : Colors.Gray500;
  const background = value ? style.background : Colors.Gray50;

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

export const PartitionCountLabels: React.FC<{
  partitionStats: LiveDataForNode['partitionStats'] | null | undefined;
}> = ({partitionStats}) => {
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

const PartitionCountLabel: React.FC<{
  status: AssetPartitionStatus;
  value: number | undefined;
  total: number | undefined;
}> = ({status, value, total}) => {
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
        style={{color: value === undefined || value === 0 ? Colors.Gray300 : Colors.Dark}}
      >
        <Icon name={style.icon} color={value ? style.border : Colors.Gray300} size={12} />
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
