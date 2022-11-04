import {gql, useApolloClient} from '@apollo/client';
import {Tooltip, Spinner, Box, Colors} from '@dagster-io/ui';
import fromPairs from 'lodash/fromPairs';
import React from 'react';

import {displayNameForAssetKey} from '../asset-graph/Utils';
import {assembleIntoSpans} from '../partitions/PartitionRangeInput';

import {AssetKey} from './types';
import {PartitionHealthQuery, PartitionHealthQueryVariables} from './types/PartitionHealthQuery';

export interface PartitionHealthData {
  assetKey: AssetKey;
  keys: string[];
  spans: {startIdx: number; endIdx: number; status: boolean}[];
  statusByPartition: {[partitionName: string]: boolean};
  indexToPct: (idx: number) => string;
}

const MAX_FETCH_AT_ONCE = 50;

// Sometimes we get a typename, sometimes we don't -- use only the path
const keyToJSON = (key: AssetKey) => JSON.stringify({path: key.path});

export function usePartitionHealthData(assetKeys: AssetKey[]) {
  const [result, setResult] = React.useState<PartitionHealthData[]>([]);
  const client = useApolloClient();

  const assetKeyJSONs = assetKeys.map(keyToJSON);
  const missingKeyJSONs = JSON.stringify(
    assetKeyJSONs
      .filter((k) => !result.some((r) => keyToJSON(r.assetKey) === k))
      .slice(0, MAX_FETCH_AT_ONCE),
  );

  React.useMemo(() => {
    const loadKeys: AssetKey[] = JSON.parse(missingKeyJSONs).map((keyJSON: string) =>
      JSON.parse(keyJSON),
    );
    if (!loadKeys.length) {
      return;
    }
    const load = async () => {
      const {data} = await client.query<PartitionHealthQuery, PartitionHealthQueryVariables>({
        query: PARTITION_HEALTH_QUERY,
        fetchPolicy: 'network-only',
        variables: {assetKeys: loadKeys},
      });

      const added: PartitionHealthData[] = [];
      for (const node of data.assetNodes) {
        const latest =
          (node.__typename === 'AssetNode' && node.materializationCountByPartition) || [];

        const keys =
          node.__typename === 'AssetNode'
            ? node.materializationCountByPartition.map(({partition}) => partition)
            : [];

        const statusByPartition = fromPairs(
          latest.map((l) => [l.partition, !!l.materializationCount]),
        );
        added.push({
          keys,
          statusByPartition,
          assetKey: node.assetKey,
          spans: assembleIntoSpans(keys, (key) => statusByPartition[key]),
          indexToPct: (idx: number) => `${((idx * 100) / keys.length).toFixed(3)}%`,
        });
      }

      setResult((result) => [...result, ...added]);
    };
    load();
  }, [client, missingKeyJSONs]);

  return result.filter((r) => assetKeyJSONs.includes(keyToJSON(r.assetKey)));
}

export const PartitionHealthSummary: React.FC<{
  assetKey: AssetKey;
  selected?: string[];
  showAssetKey?: boolean;
  data: PartitionHealthData[];
}> = ({showAssetKey, assetKey, selected, data}) => {
  const assetData = data.find((d) => JSON.stringify(d.assetKey) === JSON.stringify(assetKey));

  if (!assetData) {
    return (
      <div style={{minHeight: 55, position: 'relative'}}>
        <Spinner purpose="section" />
      </div>
    );
  }

  const {spans, keys, indexToPct} = assetData;
  const highestIndex = spans.map((s) => s.endIdx).reduce((prev, cur) => Math.max(prev, cur), 0);

  const selectedSpans = selected
    ? assembleIntoSpans(keys, (key) => selected.includes(key)).filter((s) => s.status)
    : [];

  const populated = spans
    .filter((s) => s.status === true)
    .map((s) => s.endIdx - s.startIdx + 1)
    .reduce((a, b) => a + b, 0);

  return (
    <div>
      <Box
        flex={{justifyContent: 'space-between'}}
        margin={{bottom: 4}}
        style={{fontSize: '0.8rem', color: Colors.Gray500}}
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
                left: `min(calc(100% - 2px), ${indexToPct(s.startIdx)})`,
                width: indexToPct(s.endIdx - s.startIdx + 1),
                position: 'absolute',
                top: 0,
                height: 8,
                border: `2px solid ${Colors.Blue500}`,
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
              left: `min(calc(100% - 2px), ${indexToPct(s.startIdx)})`,
              width: indexToPct(s.endIdx - s.startIdx + 1),
              minWidth: s.status ? 2 : undefined,
              position: 'absolute',
              zIndex: s.startIdx === 0 || s.endIdx === highestIndex ? 3 : s.status ? 2 : 1, //End-caps, then statuses, then missing
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
                  background: s.status ? Colors.Green500 : Colors.Gray200,
                }}
              />
            </Tooltip>
          </div>
        ))}
      </div>
      <Box
        flex={{justifyContent: 'space-between'}}
        margin={{top: 4}}
        style={{fontSize: '0.8rem', color: Colors.Gray500}}
      >
        <span>{keys[0]}</span>
        <span>{keys[keys.length - 1]}</span>
      </Box>
    </div>
  );
};

const PARTITION_HEALTH_QUERY = gql`
  query PartitionHealthQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys) {
      id
      assetKey {
        path
      }
      materializationCountByPartition {
        partition
        materializationCount
      }
    }
  }
`;
