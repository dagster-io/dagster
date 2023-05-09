import {gql, useQuery} from '@apollo/client';
import {Box, Colors, Icon, MiddleTruncate} from '@dagster-io/ui';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Timestamp} from '../app/time/Timestamp';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {
  AssetMaterializationUpstreamQuery,
  AssetMaterializationUpstreamQueryVariables,
  MaterializationUpstreamDataVersionFragment,
} from './types/AssetMaterializationUpstreamData.types';

dayjs.extend(relativeTime);

export const AssetMaterializationUpstreamData: React.FC<{
  assetKey: AssetKeyInput;
  timestamp?: string;
}> = ({assetKey, timestamp}) => {
  const result = useQuery<
    AssetMaterializationUpstreamQuery,
    AssetMaterializationUpstreamQueryVariables
  >(ASSET_MATERIALIZATION_UPSTREAM_QUERY, {
    skip: !timestamp,
    variables: {assetKey, timestamp: timestamp || ''},
  });

  const displayName = displayNameForAssetKey(assetKey);
  const entries =
    result.data?.assetNodeOrError.__typename === 'AssetNode'
      ? result.data.assetNodeOrError.assetMaterializationUsedData
      : [];

  const renderEntryAndParents = (
    entry: MaterializationUpstreamDataVersionFragment,
    depth: number,
    isFirstAtDepth: boolean,
  ): React.ReactNode[] => {
    const entryDisplayName = displayNameForAssetKey(entry.assetKey);
    const entryLink = assetDetailsPathForKey(entry.assetKey, {
      view: 'events',
      time: entry.timestamp,
    });

    return [
      <tr key={entryDisplayName}>
        <td>
          <Box flex={{gap: 4}} style={{paddingLeft: Math.max(0, depth) * 20}}>
            {isFirstAtDepth && <Icon name="arrow_indent" style={{marginLeft: -20}} />}
            <Link to={entryLink}>
              <Box flex={{gap: 4}}>
                <Icon name="asset" />
                <MiddleTruncate text={entryDisplayName} />
              </Box>
            </Link>
          </Box>
        </td>
        <td>
          <Box flex={{gap: 8}} style={{whiteSpace: 'nowrap'}}>
            <Link to={entryLink}>
              <Timestamp
                timestamp={{ms: Number(entry.timestamp)}}
                timeFormat={{showSeconds: true, showTimezone: false}}
              />
            </Link>
            <span style={{opacity: 0.7}}>
              ({dayjs(Number(entry.timestamp)).from(Number(timestamp), true)} earlier)
            </span>
          </Box>
        </td>
      </tr>,
      ...entries
        .filter((e) => displayNameForAssetKey(e.downstreamAssetKey) === entryDisplayName)
        .map((e, idx) => renderEntryAndParents(e, depth + 1, idx === 0)),
    ];
  };

  if (result.loading) {
    return (
      <AssetUpstreamDataTable>
        <tbody>
          <tr>
            <td>Loading…</td>
          </tr>
        </tbody>
      </AssetUpstreamDataTable>
    );
  }
  if (!entries.length) {
    return (
      <AssetUpstreamDataTable>
        <tbody>
          <tr>
            <td>No upstream materializations to display.</td>
          </tr>
        </tbody>
      </AssetUpstreamDataTable>
    );
  }
  return (
    <AssetUpstreamDataTable>
      <tbody>
        {entries
          .filter((e) => displayNameForAssetKey(e.downstreamAssetKey) === displayName)
          .map((e) => renderEntryAndParents(e, 0, false))}
      </tbody>
    </AssetUpstreamDataTable>
  );
};

export const ASSET_MATERIALIZATION_UPSTREAM_QUERY = gql`
  query AssetMaterializationUpstreamQuery($assetKey: AssetKeyInput!, $timestamp: String!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        assetMaterializationUsedData(timestampMillis: $timestamp) {
          ...MaterializationUpstreamDataVersionFragment
        }
      }
    }
  }

  fragment MaterializationUpstreamDataVersionFragment on MaterializationUpstreamDataVersion {
    timestamp
    assetKey {
      path
    }
    downstreamAssetKey {
      path
    }
  }
`;

const AssetUpstreamDataTable = styled.table`
  width: 100%;
  border-spacing: 0;
  border-collapse: collapse;

  tr td {
    border: 1px solid ${Colors.KeylineGray};
    padding: 8px 12px;
    font-size: 14px;
    vertical-align: top;
  }
`;
