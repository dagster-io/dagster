import {gql, useQuery} from '@apollo/client';
import {Body2, Box, Colors, Tag} from '@dagster-io/ui-components';
import React, {useContext} from 'react';
import {Link} from 'react-router-dom';

import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {LoadingSpinner} from '../../ui/Loading';
import {useFormatDateTime} from '../../ui/useFormatDateTime';
import {AssetFeatureContext} from '../AssetFeatureContext';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';
import {AssetKey} from '../types';

import {
  ASSET_CHECK_EXECUTION_FRAGMENT,
  AssetCheckDetailModal,
  MigrationRequired,
  NoChecks,
} from './AssetCheckDetailModal';
import {VirtualizedAssetCheckTable} from './VirtualizedAssetCheckTable';
import {AssetChecksQuery, AssetChecksQueryVariables} from './types/AssetChecks.types';

export const AssetChecks = ({
  lastMaterializationTimestamp,
  assetKey,
}: {
  assetKey: AssetKey;
  lastMaterializationTimestamp: string | undefined;
}) => {
  const formatDatetime = useFormatDateTime();
  const lastMaterializationDate = React.useMemo(
    () => (lastMaterializationTimestamp ? new Date(parseInt(lastMaterializationTimestamp)) : null),
    [lastMaterializationTimestamp],
  );
  const isCurrentYear = React.useMemo(
    () => lastMaterializationDate?.getFullYear() === new Date().getFullYear(),
    [lastMaterializationDate],
  );

  const queryResult = useQuery<AssetChecksQuery, AssetChecksQueryVariables>(ASSET_CHECKS_QUERY, {
    variables: {
      assetKey,
    },
  });
  const {data} = queryResult;
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const [openCheck, setOpenCheck] = useQueryPersistedState<string | undefined>({
    queryKey: 'checkDetail',
  });
  function content() {
    if (!data) {
      return <LoadingSpinner purpose="page" />;
    }
    const result = data.assetChecksOrError!;
    if (result.__typename === 'AssetCheckNeedsMigrationError') {
      return <MigrationRequired />;
    }
    const checks = result.checks;
    if (!checks.length) {
      return <NoChecks />;
    }
    return <VirtualizedAssetCheckTable assetKey={assetKey} rows={checks} />;
  }

  const {AssetChecksBanner} = useContext(AssetFeatureContext);

  return (
    <div>
      <AssetCheckDetailModal
        assetKey={assetKey}
        checkName={openCheck}
        onClose={() => {
          setOpenCheck(undefined);
        }}
      />
      <Box
        padding={{horizontal: 24, vertical: 12}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <AssetChecksBanner />
      </Box>
      <Box
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 32}}
        padding={{horizontal: 24, vertical: 16}}
        border={{side: 'bottom', color: Colors.KeylineGray, width: 1}}
      >
        <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
          <Body2>Latest materialization:</Body2>

          <Link
            to={assetDetailsPathForKey(assetKey, {
              time: lastMaterializationTimestamp,
              view: 'events',
            })}
          >
            <Tag icon="materialization">
              {lastMaterializationDate ? (
                <>
                  {formatDatetime(lastMaterializationDate, {
                    month: 'short',
                    day: 'numeric',
                    year: isCurrentYear ? undefined : 'numeric',
                  })}{' '}
                  at{' '}
                  {formatDatetime(lastMaterializationDate, {
                    hour: 'numeric',
                    minute: 'numeric',
                  })}
                </>
              ) : (
                'None'
              )}
            </Tag>
          </Link>
        </Box>
        {/* TODO: Enable once the mutations are ready */}
        {/* {data && 'checks' in data.assetChecksOrError! && data.assetChecksOrError.checks.length ? (
          <Button
            icon={<Icon name="run" />}
            onClick={() => {
              //TODO
            }}
          >
            Execute all checks
          </Button>
        ) : null} */}
      </Box>
      {content()}
    </div>
  );
};

export const ASSET_CHECKS_QUERY = gql`
  query AssetChecksQuery($assetKey: AssetKeyInput!) {
    assetChecksOrError(assetKey: $assetKey) {
      ... on AssetCheckNeedsMigrationError {
        message
      }
      ... on AssetChecks {
        checks {
          name
          description
          executionForLatestMaterialization {
            ...AssetCheckExecutionFragment
          }
        }
      }
    }
  }
  ${ASSET_CHECK_EXECUTION_FRAGMENT}
`;
