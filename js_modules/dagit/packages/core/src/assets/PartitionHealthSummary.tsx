import {gql, useQuery} from '@apollo/client';
import {Tooltip, Spinner, Box, ColorsWIP} from '@dagster-io/ui';
import {keyBy} from 'lodash';
import React from 'react';

import {displayNameForAssetKey} from '../app/Util';
import {assembleIntoSpans} from '../partitions/PartitionRangeInput';

import {AssetKey} from './types';
import {PartitionHealthQuery, PartitionHealthQueryVariables} from './types/PartitionHealthQuery';

export function usePartitionHealthData(assetKey: AssetKey) {
  const {data, loading} = useQuery<PartitionHealthQuery, PartitionHealthQueryVariables>(
    PARTITION_HEALTH_QUERY,
    {
      variables: {assetKey: {path: assetKey.path}},
      fetchPolicy: 'cache-and-network',
    },
  );

  const {spans, keys, indexToPct} = React.useMemo(() => {
    const latest =
      (data &&
        data.assetNodeOrError.__typename === 'AssetNode' &&
        data.assetNodeOrError.latestMaterializationByPartition) ||
      [];

    const keys =
      data && data.assetNodeOrError.__typename === 'AssetNode'
        ? data.assetNodeOrError.partitionKeys
        : [];

    const latestByKey = keyBy(
      latest.filter(Boolean).map((l) => l!),
      (l) => l.partition,
    );
    const spans = assembleIntoSpans(keys, (key) => key in latestByKey);

    return {
      keys,
      spans,
      indexToPct: (idx: number) => `${((idx * 100) / keys.length).toFixed(3)}%`,
    };
  }, [data]);

  return {spans, keys, indexToPct, loading};
}

export const PartitionHealthSummary: React.FC<{
  assetKey: AssetKey;
  selected?: string[];
  showAssetKey?: boolean;
}> = ({showAssetKey, assetKey, selected}) => {
  const {spans, keys, indexToPct, loading} = usePartitionHealthData(assetKey);
  const selectedSpans = selected
    ? assembleIntoSpans(keys, (key) => selected.includes(key)).filter((s) => s.status)
    : [];

  if (loading) {
    return (
      <div style={{minHeight: 55, position: 'relative'}}>
        <Spinner purpose="section" />
      </div>
    );
  }

  const populated = spans
    .filter((s) => s.status === true)
    .map((s) => s.endIdx - s.startIdx + 1)
    .reduce((a, b) => a + b, 0);

  return (
    <div>
      <Box
        flex={{justifyContent: 'space-between'}}
        margin={{bottom: 4}}
        style={{fontSize: '0.8rem', color: ColorsWIP.Gray500}}
      >
        <span>
          {showAssetKey
            ? displayNameForAssetKey(assetKey)
            : `${populated}/${keys.length} Partitions`}
        </span>
        {showAssetKey ? <span>{`${populated}/${keys.length}`}</span> : undefined}
      </Box>
      {selected && (
        <div style={{position: 'relative', width: '100%', overflowX: 'hidden', height: 10}}>
          {selectedSpans.map((s) => (
            <div
              key={s.startIdx}
              style={{
                left: indexToPct(s.startIdx),
                width: indexToPct(s.endIdx - s.startIdx + 1),
                position: 'absolute',
                top: 0,
                height: 8,
                border: `2px solid ${ColorsWIP.Blue500}`,
                borderBottom: 0,
              }}
            />
          ))}
        </div>
      )}
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: 14,
          borderRadius: 6,
          overflow: 'hidden',
        }}
      >
        {spans.map((s) => (
          <div
            key={s.startIdx}
            style={{
              left: indexToPct(s.startIdx),
              width: indexToPct(s.endIdx - s.startIdx + 1),
              minWidth: 2,
              position: 'absolute',
              zIndex: s.status === false ? 2 : 1,
              top: 0,
            }}
          >
            <Tooltip
              display="block"
              content={
                s.startIdx === s.endIdx
                  ? `Partition ${keys[s.startIdx]} is ${s.status ? 'up-to-date' : 'missing'}`
                  : `Partitions ${keys[s.startIdx]} through ${keys[s.endIdx]} are ${
                      s.status ? 'up-to-date' : 'missing'
                    }`
              }
            >
              <div
                style={{
                  width: '100%',
                  height: 14,
                  outline: 'none',
                  background: s.status ? ColorsWIP.Green500 : ColorsWIP.Gray200,
                }}
              />
            </Tooltip>
          </div>
        ))}
      </div>
      <Box
        flex={{justifyContent: 'space-between'}}
        margin={{top: 4}}
        style={{fontSize: '0.8rem', color: ColorsWIP.Gray500}}
      >
        <span>{keys[0]}</span>
        <span>{keys[keys.length - 1]}</span>
      </Box>
    </div>
  );
};

const PARTITION_HEALTH_QUERY = gql`
  query PartitionHealthQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        partitionKeys
        latestMaterializationByPartition {
          partition
          materializationEvent {
            timestamp
          }
        }
      }
    }
  }
`;
