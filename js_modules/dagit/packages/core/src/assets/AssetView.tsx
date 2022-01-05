import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {QueryCountdown} from '../app/QueryCountdown';
import {displayNameForAssetKey} from '../app/Util';
import {Timestamp} from '../app/time/Timestamp';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useDidLaunchEvent} from '../runs/RunUtils';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {Spinner} from '../ui/Spinner';
import {LaunchAssetExecutionButton} from '../workspace/asset-graph/LaunchAssetExecutionButton';
import {
  buildGraphDataFromSingleNode,
  buildLiveData,
  IN_PROGRESS_RUNS_FRAGMENT,
  LiveData,
} from '../workspace/asset-graph/Utils';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {AssetMaterializations} from './AssetMaterializations';
import {AssetNodeDefinition, ASSET_NODE_DEFINITION_FRAGMENT} from './AssetNodeDefinition';
import {AssetPageHeader} from './AssetPageHeader';
import {AssetKey} from './types';
import {
  AssetNodeDefinitionRunsQuery,
  AssetNodeDefinitionRunsQueryVariables,
} from './types/AssetNodeDefinitionRunsQuery';
import {AssetQuery, AssetQueryVariables} from './types/AssetQuery';

interface Props {
  assetKey: AssetKey;
}

export interface AssetViewParams {
  xAxis?: 'partition' | 'time';
  asOf?: string;
}

export const AssetView: React.FC<Props> = ({assetKey}) => {
  useDocumentTitle(`Asset: ${displayNameForAssetKey(assetKey)}`);

  const [params, setParams] = useQueryPersistedState<AssetViewParams>({});
  const [navigatedDirectlyToTime, setNavigatedDirectlyToTime] = React.useState(() =>
    Boolean(params.asOf),
  );

  const queryResult = useQuery<AssetQuery, AssetQueryVariables>(ASSET_QUERY, {
    variables: {assetKey: {path: assetKey.path}},
    notifyOnNetworkStatusChange: true,
    pollInterval: 5 * 1000,
  });

  // Refresh immediately when a run is launched from this page
  useDidLaunchEvent(queryResult.refetch);

  const {assetOrError} = queryResult.data || queryResult.previousData || {};
  const asset = assetOrError && assetOrError.__typename === 'Asset' ? assetOrError : null;
  const definition = asset?.definition;
  const lastMaterializedAt = asset?.assetMaterializations[0]?.materializationEvent.timestamp;
  const repoAddress = definition
    ? buildRepoAddress(definition.repository.name, definition.repository.location.name)
    : null;

  const bonusResult = useQuery<AssetNodeDefinitionRunsQuery, AssetNodeDefinitionRunsQueryVariables>(
    ASSET_NODE_DEFINITION_RUNS_QUERY,
    {
      skip: !repoAddress,
      variables: {
        repositorySelector: {
          repositoryLocationName: repoAddress ? repoAddress.location : '',
          repositoryName: repoAddress ? repoAddress.name : '',
        },
      },
      notifyOnNetworkStatusChange: true,
      pollInterval: 5 * 1000,
    },
  );

  let liveDataByNode: LiveData = {};

  if (definition) {
    const inProgressRuns =
      bonusResult.data?.repositoryOrError.__typename === 'Repository'
        ? bonusResult.data.repositoryOrError.inProgressRunsByStep
        : [];

    const nodesWithLatestMaterialization = [
      definition,
      ...definition.dependencies.map((d) => d.asset),
      ...definition.dependedBy.map((d) => d.asset),
    ];
    liveDataByNode = buildLiveData(
      buildGraphDataFromSingleNode(definition),
      nodesWithLatestMaterialization,
      inProgressRuns,
    );
  }

  return (
    <div>
      <AssetPageHeader
        assetKey={assetKey}
        repoAddress={repoAddress}
        right={
          <Box style={{margin: '-4px 0'}} flex={{gap: 8, alignItems: 'baseline'}}>
            <Box margin={{top: 4}}>
              <QueryCountdown pollInterval={5 * 1000} queryResult={queryResult} />
            </Box>
            {definition && definition.jobs.length > 0 && repoAddress && (
              <LaunchAssetExecutionButton
                assets={[definition]}
                assetJobName={definition.jobs[0].name}
                title={lastMaterializedAt ? 'Rematerialize' : 'Materialize'}
                repoAddress={repoAddress}
              />
            )}
          </Box>
        }
      />

      <div>
        {queryResult.loading && !queryResult.previousData ? (
          <Box
            style={{height: 390}}
            flex={{direction: 'row', justifyContent: 'center', alignItems: 'center'}}
          >
            <Spinner purpose="section" />
          </Box>
        ) : navigatedDirectlyToTime ? (
          <Box
            padding={{vertical: 16, horizontal: 24}}
            border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
          >
            <HistoricalViewAlert
              asOf={params.asOf}
              onClick={() => setNavigatedDirectlyToTime(false)}
              hasDefinition={!!definition}
            />
          </Box>
        ) : definition && repoAddress ? (
          <AssetNodeDefinition
            repoAddress={repoAddress}
            assetNode={definition}
            liveDataByNode={liveDataByNode}
          />
        ) : undefined}
      </div>
      <AssetMaterializations
        assetKey={assetKey}
        assetLastMaterializedAt={lastMaterializedAt}
        params={params}
        paramsTimeWindowOnly={navigatedDirectlyToTime}
        setParams={setParams}
        liveData={definition ? liveDataByNode[definition.id] : undefined}
      />
    </div>
  );
};

const ASSET_QUERY = gql`
  query AssetQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }

        assetMaterializations(limit: 1) {
          materializationEvent {
            timestamp
          }
        }

        definition {
          id
          repository {
            id
            name
            location {
              id
              name
            }
          }
          ...AssetNodeDefinitionFragment
        }
      }
    }
  }
  ${ASSET_NODE_DEFINITION_FRAGMENT}
`;

const ASSET_NODE_DEFINITION_RUNS_QUERY = gql`
  query AssetNodeDefinitionRunsQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on Repository {
        id
        name
        inProgressRunsByStep {
          ...InProgressRunsFragment
        }
      }
    }
  }
  ${IN_PROGRESS_RUNS_FRAGMENT}
`;

const HistoricalViewAlert: React.FC<{
  asOf: string | undefined;
  onClick: () => void;
  hasDefinition: boolean;
}> = ({asOf, onClick, hasDefinition}) => (
  <Alert
    intent="info"
    title={
      <span>
        This is a historical view of materializations as of{' '}
        <span style={{fontWeight: 600}}>
          <Timestamp
            timestamp={{ms: Number(asOf)}}
            timeFormat={{showSeconds: true, showTimezone: true}}
          />
        </span>
        .
      </span>
    }
    description={
      <ButtonLink onClick={onClick} underline="always">
        {hasDefinition
          ? 'Show definition and latest materializations'
          : 'Show latest materializations'}
      </ButtonLink>
    }
  />
);
