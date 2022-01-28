import {gql, useQuery} from '@apollo/client';
import {Alert, Box, ButtonLink, ColorsWIP, Spinner} from '@dagster-io/ui';
import * as React from 'react';

import {QueryCountdown} from '../app/QueryCountdown';
import {displayNameForAssetKey} from '../app/Util';
import {Timestamp} from '../app/time/Timestamp';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useDidLaunchEvent} from '../runs/RunUtils';
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
  partition?: string;
  time?: string;
  asOf?: string;
}

export const AssetView: React.FC<Props> = ({assetKey}) => {
  useDocumentTitle(`Asset: ${displayNameForAssetKey(assetKey)}`);

  const [params, setParams] = useQueryPersistedState<AssetViewParams>({});

  const queryResult = useQuery<AssetQuery, AssetQueryVariables>(ASSET_QUERY, {
    variables: {assetKey: {path: assetKey.path}},
    notifyOnNetworkStatusChange: true,
    pollInterval: 5 * 1000,
  });

  // Refresh immediately when a run is launched from this page
  useDidLaunchEvent(queryResult.refetch);

  const {assetOrError} = queryResult.data || queryResult.previousData || {};
  const asset = assetOrError && assetOrError.__typename === 'Asset' ? assetOrError : null;
  const lastMaterializedAt = asset?.assetMaterializations[0]?.timestamp;
  const definition = asset?.definition;

  const repoAddress = definition
    ? buildRepoAddress(definition.repository.name, definition.repository.location.name)
    : null;

  const inProgressRunsQuery = useQuery<
    AssetNodeDefinitionRunsQuery,
    AssetNodeDefinitionRunsQueryVariables
  >(ASSET_NODE_DEFINITION_RUNS_QUERY, {
    skip: !repoAddress,
    variables: {
      repositorySelector: {
        repositoryLocationName: repoAddress ? repoAddress.location : '',
        repositoryName: repoAddress ? repoAddress.name : '',
      },
    },
    notifyOnNetworkStatusChange: true,
    pollInterval: 5 * 1000,
  });

  let liveDataByNode: LiveData = {};

  if (definition) {
    const inProgressRuns =
      inProgressRunsQuery.data?.repositoryOrError.__typename === 'Repository'
        ? inProgressRunsQuery.data.repositoryOrError.inProgressRunsByStep
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

  // Avoid thrashing the materializations UI (which chooses a different default query based on whether
  // data is partitioned) by waiting for the definition to be loaded. (null OR a valid definition)
  const isDefinitionLoaded = definition !== undefined;

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
        ) : params.asOf ? (
          <Box
            padding={{vertical: 16, horizontal: 24}}
            border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
          >
            <HistoricalViewAlert
              asOf={params.asOf}
              onClick={() => setParams({asOf: undefined, time: params.asOf})}
              hasDefinition={!!definition}
            />
          </Box>
        ) : definition ? (
          <AssetNodeDefinition assetNode={definition} liveDataByNode={liveDataByNode} />
        ) : undefined}
      </div>
      {isDefinitionLoaded && (
        <AssetMaterializations
          assetKey={assetKey}
          assetLastMaterializedAt={lastMaterializedAt}
          assetHasDefinedPartitions={!!definition?.partitionDefinition}
          params={params}
          paramsTimeWindowOnly={!!params.asOf}
          setParams={setParams}
          liveData={definition ? liveDataByNode[definition.id] : undefined}
        />
      )}
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
          timestamp
        }

        definition {
          id
          partitionDefinition
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
