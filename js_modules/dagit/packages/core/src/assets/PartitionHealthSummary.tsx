import {Spinner, Box, Colors, Tooltip} from '@dagster-io/ui';
import React from 'react';

import {displayNameForAssetKey} from '../asset-graph/Utils';
import {assembleIntoSpans} from '../partitions/PartitionRangeInput';
import {PartitionState} from '../partitions/PartitionStatus';

import {AssetKey} from './types';
import {PartitionHealthData} from './usePartitionHealthData';

export const PartitionHealthSummary: React.FC<{
  assetKey: AssetKey;
  selected?: {partitionKey: string}[];
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

  const timeDimension = assetData.dimensions[0];
  const keys = timeDimension.partitionKeys;

  // todo support for partial state on summary bar
  const spans = assembleIntoSpans(
    keys,
    (key) => assetData.stateForPartialKey([key]) === PartitionState.SUCCESS,
  );

  const selectedKeys = selected?.map((s) => s.partitionKey);
  const selectedSpans = selectedKeys
    ? assembleIntoSpans(keys, (key) => selectedKeys.includes(key)).filter((s) => s.status)
    : [];

  const populated = spans
    .filter((s) => s.status === true)
    .map((s) => s.endIdx - s.startIdx + 1)
    .reduce((a, b) => a + b, 0);

  const indexToPct = (idx: number) => `${((idx * 100) / keys.length).toFixed(3)}%`;
  const highestIndex = spans.map((s) => s.endIdx).reduce((prev, cur) => Math.max(prev, cur), 0);

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
