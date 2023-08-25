import {gql, useQuery} from '@apollo/client';
import {Body2, Box, Colors, Tag} from '@dagster-io/ui-components';
import React from 'react';
import {useHistory, useLocation} from 'react-router';

import {LoadingSpinner} from '../../ui/Loading';
import {useFormatDateTime} from '../../ui/useFormatDateTime';
import {AssetKey, AssetDefinition} from '../types';

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
  lastMaterializationRunId,
  assetKey,
}: {
  definition: AssetDefinition;
  assetKey: AssetKey;
  lastMaterializationTimestamp: string | undefined;
  lastMaterializationRunId: string | undefined;
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

  const {data} = useQuery<AssetChecksQuery, AssetChecksQueryVariables>(ASSET_CHECKS_QUERY, {
    variables: {
      assetKey,
    },
  });

  const {search} = useLocation();
  const check_detail = React.useMemo(() => new URLSearchParams(search).get('check_detail'), [
    search,
  ]);

  const [openCheck, setOpenCheck] = React.useState<string | undefined | null>();
  React.useEffect(() => {
    setOpenCheck(check_detail);
  }, [check_detail]);

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
    return (
      <VirtualizedAssetCheckTable
        rows={checks}
        lastMaterializationRunId={lastMaterializationRunId}
      />
    );
  }

  const history = useHistory();

  return (
    <div>
      <AssetCheckDetailModal
        assetKey={assetKey}
        checkName={openCheck}
        onClose={() => {
          const searchParams = new URLSearchParams(location.search);
          searchParams.delete('check_detail');
          const newSearch = searchParams.toString();
          const newLocation = {
            ...location,
            search: newSearch ? `?${newSearch}` : '',
          };
          history.push(newLocation);
        }}
      />
      <Box
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 32}}
        padding={{horizontal: 24, vertical: 16}}
        border={{side: 'bottom', color: Colors.KeylineGray, width: 1}}
      >
        <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
          <Body2>Latest materialization:</Body2>

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
          executions(limit: 1, cursor: "") {
            ...AssetCheckExecutionFragment
          }
        }
      }
    }
  }
  ${ASSET_CHECK_EXECUTION_FRAGMENT}
`;
