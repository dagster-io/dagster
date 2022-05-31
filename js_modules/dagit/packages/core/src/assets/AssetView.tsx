import {gql, useQuery} from '@apollo/client';
import {
  Alert,
  Box,
  ButtonLink,
  Colors,
  NonIdealState,
  Spinner,
  Tab,
  Tabs,
  Tag,
} from '@dagster-io/ui';
import * as React from 'react';

import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useMergedRefresh,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {Timestamp} from '../app/time/Timestamp';
import {
  buildGraphDataFromSingleNode,
  buildLiveData,
  LiveData,
  displayNameForAssetKey,
  toGraphId,
} from '../asset-graph/Utils';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RepositoryLink} from '../nav/RepositoryLink';
import {useDidLaunchEvent} from '../runs/RunUtils';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {AssetEvents} from './AssetEvents';
import {AssetNodeDefinition, ASSET_NODE_DEFINITION_FRAGMENT} from './AssetNodeDefinition';
import {AssetNodeInstigatorTag, ASSET_NODE_INSTIGATORS_FRAGMENT} from './AssetNodeInstigatorTag';
import {AssetPageHeader} from './AssetPageHeader';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {AssetKey} from './types';
import {
  AssetNodeDefinitionLiveQuery,
  AssetNodeDefinitionLiveQueryVariables,
} from './types/AssetNodeDefinitionLiveQuery';
import {AssetQuery, AssetQueryVariables} from './types/AssetQuery';

interface Props {
  assetKey: AssetKey;
}

export interface AssetViewParams {
  view?: 'activity' | 'definition';
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
  });

  const {assetOrError} = queryResult.data || queryResult.previousData || {};
  const asset = assetOrError && assetOrError.__typename === 'Asset' ? assetOrError : null;
  const lastMaterializedAt = asset?.assetMaterializations[0]?.timestamp;
  const viewingMostRecent = !params.asOf || Number(lastMaterializedAt) <= Number(params.asOf);

  const definition = asset?.definition;

  const repoAddress = definition
    ? buildRepoAddress(definition.repository.name, definition.repository.location.name)
    : null;

  const liveQueryResult = useQuery<
    AssetNodeDefinitionLiveQuery,
    AssetNodeDefinitionLiveQueryVariables
  >(ASSET_NODE_DEFINITION_LIVE_QUERY, {
    skip: !repoAddress,
    variables: {
      assetKeys: [assetKey],
    },
    notifyOnNetworkStatusChange: true,
  });

  const refreshState = useMergedRefresh(
    useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS),
    useQueryRefreshAtInterval(liveQueryResult, FIFTEEN_SECONDS),
  );

  // Refresh immediately when a run is launched from this page
  useDidLaunchEvent(queryResult.refetch);
  useDidLaunchEvent(liveQueryResult.refetch);

  let liveDataByNode: LiveData = {};

  const assetsLatestInfo = liveQueryResult.data ? liveQueryResult.data.assetsLatestInfo : null;

  if (definition && assetsLatestInfo) {
    const nodesWithLatestMaterialization = [
      definition,
      ...definition.dependencies.map((d) => d.asset),
      ...definition.dependedBy.map((d) => d.asset),
    ];
    liveDataByNode = buildLiveData(
      buildGraphDataFromSingleNode(definition),
      nodesWithLatestMaterialization,
      assetsLatestInfo,
    );
  }

  // Avoid thrashing the materializations UI (which chooses a different default query based on whether
  // data is partitioned) by waiting for the definition to be loaded. (null OR a valid definition)
  const isDefinitionLoaded = definition !== undefined;

  return (
    <div>
      <AssetPageHeader
        assetKey={assetKey}
        tags={
          <>
            {repoAddress ? (
              <Tag icon="asset">
                Asset in <RepositoryLink repoAddress={repoAddress} />
              </Tag>
            ) : (
              <Tag icon="asset">Asset</Tag>
            )}
            {definition && repoAddress && (
              <AssetNodeInstigatorTag assetNode={definition} repoAddress={repoAddress} />
            )}
          </>
        }
        tabs={
          <Tabs size="large" selectedTabId={params.view || 'activity'}>
            <Tab
              id="activity"
              title="Activity"
              onClick={() => setParams({...params, view: 'activity'})}
            />
            <Tab
              id="definition"
              title="Definition"
              onClick={() => setParams({...params, view: 'definition'})}
              disabled={!definition}
            />
          </Tabs>
        }
        right={
          <Box style={{margin: '-4px 0'}} flex={{gap: 8, alignItems: 'baseline'}}>
            <Box margin={{top: 4}}>
              <QueryRefreshCountdown refreshState={refreshState} />
            </Box>
            {definition && definition.jobNames.length > 0 && repoAddress && (
              <LaunchAssetExecutionButton
                assets={[definition]}
                upstreamAssetKeys={definition.dependencies.map((d) => d.asset.assetKey)}
                preferredJobName={definition.jobNames[0]}
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
            <Spinner purpose="page" />
          </Box>
        ) : viewingMostRecent ? null : (
          <Box
            padding={{vertical: 16, horizontal: 24}}
            border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
          >
            <HistoricalViewAlert
              asOf={params.asOf}
              onClick={() => setParams({asOf: undefined, time: params.asOf})}
              hasDefinition={!!definition}
            />
          </Box>
        )}
      </div>
      {isDefinitionLoaded &&
        (params.view === 'definition' ? (
          definition ? (
            <AssetNodeDefinition assetNode={definition} liveDataByNode={liveDataByNode} />
          ) : (
            <Box padding={{vertical: 32}}>
              <NonIdealState
                title="No definition"
                description="This asset doesn't have a software definition in any of your loaded repositories."
                icon="materialization"
              />
            </Box>
          )
        ) : (
          <AssetEvents
            assetKey={assetKey}
            assetLastMaterializedAt={lastMaterializedAt}
            assetHasDefinedPartitions={!!definition?.partitionDefinition}
            params={params}
            paramsTimeWindowOnly={!!params.asOf}
            setParams={setParams}
            liveData={definition ? liveDataByNode[toGraphId(definition.assetKey)] : undefined}
          />
        ))}
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

          ...AssetNodeInstigatorsFragment
          ...AssetNodeDefinitionFragment
        }
      }
    }
  }
  ${ASSET_NODE_INSTIGATORS_FRAGMENT}
  ${ASSET_NODE_DEFINITION_FRAGMENT}
`;

const ASSET_NODE_DEFINITION_LIVE_QUERY = gql`
  query AssetNodeDefinitionLiveQuery($assetKeys: [AssetKeyInput!]) {
    assetsLatestInfo(assetKeys: $assetKeys) {
      assetKey {
        path
      }
      unstartedRunIds
      inProgressRunIds
      latestRun {
        status
        id
      }
    }
  }
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
