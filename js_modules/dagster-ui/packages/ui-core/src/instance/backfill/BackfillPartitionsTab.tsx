import {gql, useApolloClient} from '@apollo/client';
import {Box, ButtonLink, Colors, NonIdealState, Table, Tag} from '@dagster-io/ui-components';
import React from 'react';
import {Link, useHistory} from 'react-router-dom';

import {BackfillDetailsBackfillFragment} from './types/BackfillPage.types';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {asAssetKeyInput} from '../../assets/asInput';
import {assetDetailsPathForKey} from '../../assets/assetDetailsPathForKey';
import {AssetViewParams} from '../../assets/types';
import {AssetKey, RunStatus} from '../../graphql/types';
import {RunFilterToken, runsPathWithFilters} from '../../runs/RunsFilterInput';
import {testId} from '../../testing/testId';
import {
  BackfillPartitionsForAssetKeyQuery,
  BackfillPartitionsForAssetKeyQueryVariables,
} from '../backfill/types/BackfillPage.types';

export const BackfillPartitionsTab = ({backfill}: {backfill: BackfillDetailsBackfillFragment}) => {
  const client = useApolloClient();
  const history = useHistory();

  function getRunsUrl(status: 'inProgress' | 'complete' | 'failed' | 'targeted') {
    const filters: RunFilterToken[] = [
      {
        token: 'tag',
        value: `dagster/backfill=${backfill.id}`,
      },
    ];
    switch (status) {
      case 'inProgress':
        filters.push(
          {
            token: 'status',
            value: RunStatus.STARTED,
          },
          {
            token: 'status',
            value: RunStatus.QUEUED,
          },
          {
            token: 'status',
            value: RunStatus.STARTING,
          },
          {
            token: 'status',
            value: RunStatus.CANCELING,
          },
          {
            token: 'status',
            value: RunStatus.NOT_STARTED,
          },
        );
        break;
      case 'complete':
        filters.push({
          token: 'status',
          value: RunStatus.SUCCESS,
        });
        break;
      case 'failed':
        filters.push({
          token: 'status',
          value: RunStatus.FAILURE,
        });
        filters.push({
          token: 'status',
          value: RunStatus.CANCELED,
        });
        break;
    }
    return runsPathWithFilters(filters);
  }

  const onShowAssetDetails = async (assetKey: AssetKey, isPartitioned: boolean) => {
    let params: AssetViewParams = {};

    if (isPartitioned) {
      const resp = await client.query<
        BackfillPartitionsForAssetKeyQuery,
        BackfillPartitionsForAssetKeyQueryVariables
      >({
        query: BACKFILL_PARTITIONS_FOR_ASSET_KEY_QUERY,
        variables: {backfillId: backfill.id, assetKey: asAssetKeyInput(assetKey)},
      });
      const data =
        resp.data.partitionBackfillOrError.__typename === 'PartitionBackfill'
          ? resp.data.partitionBackfillOrError.partitionsTargetedForAssetKey
          : null;

      if (data && data.ranges?.length) {
        params = {default_range: data.ranges.map((r) => `[${r.start}...${r.end}]`).join(',')};
      }
    }
    return history.push(assetDetailsPathForKey(assetKey, params));
  };

  if (!backfill.assetBackfillData?.assetBackfillStatuses.length) {
    return (
      <Box margin={48}>
        <NonIdealState
          title="Partition statuses unavailable"
          description="Dagster was unable to load per-partition statuses. This may occur if the backfilled assets or jobs no longer exist in your loaded code locations."
        />
      </Box>
    );
  }

  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '50%'}}>Asset name</th>
          <th>
            <Link to={getRunsUrl('targeted')}>Partitions targeted</Link>
          </th>
          <th>
            <Link to={getRunsUrl('inProgress')}>In progress</Link>
          </th>
          <th>
            <Link to={getRunsUrl('complete')}>Completed</Link>
          </th>
          <th>
            <Link to={getRunsUrl('failed')}>Failed</Link>
          </th>
        </tr>
      </thead>
      <tbody>
        {backfill.assetBackfillData?.assetBackfillStatuses.map((asset) => {
          let targeted;
          let inProgress;
          let completed;
          let failed;
          if (asset.__typename === 'AssetPartitionsStatusCounts') {
            targeted = asset.numPartitionsTargeted;
            inProgress = asset.numPartitionsInProgress;
            completed = asset.numPartitionsMaterialized;
            failed = asset.numPartitionsFailed;
          } else {
            targeted = 1;
            failed = asset.failed ? 1 : 0;
            inProgress = asset.inProgress ? 1 : 0;
            completed = asset.materialized ? 1 : 0;
          }
          return (
            <tr
              key={tokenForAssetKey(asset.assetKey)}
              data-testid={testId(`backfill-asset-row-${tokenForAssetKey(asset.assetKey)}`)}
            >
              <td>
                <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                  <div>
                    <ButtonLink
                      onClick={() =>
                        onShowAssetDetails(
                          asset.assetKey,
                          asset.__typename === 'AssetPartitionsStatusCounts',
                        )
                      }
                    >
                      {asset.assetKey.path.join('/')}
                    </ButtonLink>
                  </div>
                  <div>
                    <StatusBar
                      targeted={targeted}
                      inProgress={inProgress}
                      completed={completed}
                      failed={failed}
                    />
                  </div>
                </Box>
              </td>
              {asset.__typename === 'AssetPartitionsStatusCounts' ? (
                <>
                  <td>{targeted}</td>
                  <td>{inProgress}</td>
                  <td>{completed}</td>
                  <td>{failed}</td>
                </>
              ) : (
                <>
                  <td>-</td>
                  <td>
                    {inProgress ? (
                      <Tag icon="spinner" intent="primary">
                        In progress
                      </Tag>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td>{completed ? <Tag intent="success">Completed</Tag> : '-'}</td>
                  <td>{failed ? <Tag intent="danger">Failed</Tag> : '-'}</td>
                </>
              )}
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
};

export const BACKFILL_PARTITIONS_FOR_ASSET_KEY_QUERY = gql`
  query BackfillPartitionsForAssetKey($backfillId: String!, $assetKey: AssetKeyInput!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        id
        partitionsTargetedForAssetKey(assetKey: $assetKey) {
          partitionKeys
          ranges {
            start
            end
          }
        }
      }
    }
  }
`;

function StatusBar({
  targeted,
  inProgress,
  completed,
  failed,
}: {
  targeted: number;
  inProgress: number;
  completed: number;
  failed: number;
}) {
  return (
    <div
      style={{
        borderRadius: '8px',
        backgroundColor: Colors.backgroundLight(),
        display: 'grid',
        gridTemplateColumns: `${(100 * completed) / targeted}% ${(100 * failed) / targeted}% ${
          (100 * inProgress) / targeted
        }%`,
        gridTemplateRows: '100%',
        height: '12px',
        width: '200px',
        overflow: 'hidden',
      }}
    >
      <div style={{background: Colors.accentGreen()}} />
      <div style={{background: Colors.accentRed()}} />
      <div style={{background: Colors.accentBlue()}} />
    </div>
  );
}
