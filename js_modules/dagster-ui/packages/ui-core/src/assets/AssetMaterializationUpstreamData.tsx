import {gql, useQuery} from '@apollo/client';
import {Box, Caption, Colors, Icon, MiddleTruncate} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {Timestamp} from '../app/time/Timestamp';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {
  AssetMaterializationUpstreamTableFragment,
  AssetMaterializationUpstreamQuery,
  AssetMaterializationUpstreamQueryVariables,
  MaterializationUpstreamDataVersionFragment,
} from './types/AssetMaterializationUpstreamData.types';

dayjs.extend(relativeTime);

export const AssetMaterializationUpstreamTable = ({
  data,
  assetKey,
  maximumLagMinutes,
  relativeTo,
}: {
  data: AssetMaterializationUpstreamTableFragment | undefined;
  assetKey: AssetKeyInput;
  relativeTo: number | 'now';
  maximumLagMinutes?: number; // pass to get red "late" highlighting
}) => {
  const displayName = displayNameForAssetKey(assetKey);

  if (!data) {
    return (
      <TableContainer>
        <tbody>
          <tr>
            <td>Loading…</td>
          </tr>
        </tbody>
      </TableContainer>
    );
  }
  if (!data.assetMaterializationUsedData.length) {
    return (
      <TableContainer>
        <tbody>
          <tr>
            <td>No upstream materializations to display.</td>
          </tr>
        </tbody>
      </TableContainer>
    );
  }

  const seen = new Set<string>();

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

    // Safeguard against infinite loops in this code that could be caused by the
    // API returning an entry where assetKey === downstreamAssetKey
    if (seen.has(entryDisplayName)) {
      return [];
    }
    seen.add(entryDisplayName);

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
          <Box flex={{gap: 8, justifyContent: 'space-between'}} style={{whiteSpace: 'nowrap'}}>
            <Link to={entryLink}>
              <Timestamp
                timestamp={{ms: Number(entry.timestamp)}}
                timeFormat={{showSeconds: true, showTimezone: false}}
              />
            </Link>
            <TimeSinceWithOverdueColor
              timestamp={Number(entry.timestamp)}
              maximumLagMinutes={maximumLagMinutes}
              relativeTo={relativeTo}
            />
          </Box>
        </td>
      </tr>,
      ...data.assetMaterializationUsedData
        .filter((e) => displayNameForAssetKey(e.downstreamAssetKey) === entryDisplayName)
        .map((e, idx) => renderEntryAndParents(e, depth + 1, idx === 0)),
    ];
  };

  return (
    <TableContainer>
      <tbody>
        {data.assetMaterializationUsedData
          .filter((e) => displayNameForAssetKey(e.downstreamAssetKey) === displayName)
          .map((e) => renderEntryAndParents(e, 0, false))}
      </tbody>
    </TableContainer>
  );
};

export const ASSET_MATERIALIZATION_UPSTREAM_TABLE_FRAGMENT = gql`
  fragment AssetMaterializationUpstreamTableFragment on AssetNode {
    assetMaterializationUsedData(timestampMillis: $timestamp) {
      ...MaterializationUpstreamDataVersionFragment
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

export const AssetMaterializationUpstreamData = ({
  assetKey,
  timestamp = '',
}: {
  assetKey: AssetKeyInput;
  timestamp?: string;
}) => {
  const result = useQuery<
    AssetMaterializationUpstreamQuery,
    AssetMaterializationUpstreamQueryVariables
  >(ASSET_MATERIALIZATION_UPSTREAM_QUERY, {
    variables: {assetKey: {path: assetKey.path}, timestamp},
    skip: !timestamp,
  });

  if (!timestamp) {
    return <Caption color={Colors.Gray500}>None</Caption>;
  }

  const data =
    result.data?.assetNodeOrError.__typename === 'AssetNode'
      ? result.data.assetNodeOrError
      : undefined;

  return (
    <AssetMaterializationUpstreamTable
      relativeTo={Number(timestamp)}
      assetKey={assetKey}
      data={data}
    />
  );
};

export const TimeSinceWithOverdueColor = ({
  timestamp,
  maximumLagMinutes,
  relativeTo = Date.now(),
}: {
  timestamp: number;
  maximumLagMinutes?: number;
  relativeTo?: number | 'now';
}) => {
  const lagMinutes = ((relativeTo === 'now' ? Date.now() : relativeTo) - timestamp) / (60 * 1000);
  const isOverdue = maximumLagMinutes && lagMinutes > maximumLagMinutes;

  return relativeTo === 'now' ? (
    <span style={{color: isOverdue ? Colors.Red700 : Colors.Gray700}}>
      ({dayjs(timestamp).fromNow()})
    </span>
  ) : (
    <span style={{color: isOverdue ? Colors.Red700 : Colors.Gray700}}>
      ({dayjs(Number(timestamp)).from(relativeTo, true)} earlier)
    </span>
  );
};

export const ASSET_MATERIALIZATION_UPSTREAM_QUERY = gql`
  query AssetMaterializationUpstreamQuery($assetKey: AssetKeyInput!, $timestamp: String!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        ...AssetMaterializationUpstreamTableFragment
      }
    }
  }
  ${ASSET_MATERIALIZATION_UPSTREAM_TABLE_FRAGMENT}
`;

const TableContainer = styled.table`
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
