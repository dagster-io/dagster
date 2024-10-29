import {Box, Colors, Icon} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Link} from 'react-router-dom';

import {gql, useQuery} from '../apollo-client';
import {
  RunningBackfillsNoticeQuery,
  RunningBackfillsNoticeQueryVariables,
} from './types/RunningBackfillsNotice.types';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';

export const RunningBackfillsNotice = ({assetSelection}: {assetSelection: AssetKeyInput[]}) => {
  const queryResult = useQuery<RunningBackfillsNoticeQuery, RunningBackfillsNoticeQueryVariables>(
    RUNNING_BACKFILLS_NOTICE_QUERY,
  );
  const {data} = queryResult;

  const runningBackfills =
    data?.partitionBackfillsOrError.__typename === 'PartitionBackfills'
      ? data.partitionBackfillsOrError.results
      : [];

  const assetSelectionTokens = useMemo(
    () => new Set(assetSelection.map(tokenForAssetKey)),
    [assetSelection],
  );

  const runningBackfillCount = runningBackfills.filter((r) =>
    r.assetSelection?.some((a) => assetSelectionTokens.has(tokenForAssetKey(a))),
  ).length;

  if (runningBackfillCount === 0) {
    return <span />;
  }

  return (
    <div style={{color: Colors.textLight(), maxWidth: 350}}>
      {runningBackfillCount === 1
        ? `Note: A backfill has been requested and may be refreshing displayed assets. `
        : `Note: ${runningBackfillCount} backfills have been requested and may be refreshing displayed assets. `}
      <Link to="/overview/backfills" target="_blank">
        <Box flex={{gap: 4, display: 'inline-flex', alignItems: 'center'}}>
          View <Icon name="open_in_new" color={Colors.linkDefault()} />
        </Box>
      </Link>
    </div>
  );
};

export const RUNNING_BACKFILLS_NOTICE_QUERY = gql`
  query RunningBackfillsNoticeQuery {
    partitionBackfillsOrError(status: REQUESTED) {
      ... on PartitionBackfills {
        results {
          id
          partitionSetName
          assetSelection {
            path
          }
        }
      }
    }
  }
`;
