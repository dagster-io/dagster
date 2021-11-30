import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {Timestamp} from '../app/time/Timestamp';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {Spinner} from '../ui/Spinner';
import {useRepositoryOptions} from '../workspace/WorkspaceContext';
import {assetKeyToString, IN_PROGRESS_RUNS_FRAGMENT} from '../workspace/asset-graph/Utils';
import {findRepoContainingPipeline} from '../workspace/findRepoContainingPipeline';

import {AssetMaterializations} from './AssetMaterializations';
import {AssetNodeDefinition, ASSET_NODE_DEFINITION_FRAGMENT} from './AssetNodeDefinition';
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
  useDocumentTitle(`Asset: ${assetKeyToString(assetKey)}`);

  const [params, setParams] = useQueryPersistedState<AssetViewParams>({});
  const [navigatedDirectlyToTime, setNavigatedDirectlyToTime] = React.useState(() =>
    Boolean(params.asOf),
  );

  const {data, loading} = useQuery<AssetQuery, AssetQueryVariables>(ASSET_QUERY, {
    variables: {assetKey: {path: assetKey.path}},
    pollInterval: 5 * 1000,
  });

  const definition =
    data?.assetOrError && data.assetOrError.__typename === 'Asset'
      ? data.assetOrError.definition
      : null;

  const {options} = useRepositoryOptions();
  const [repo] = definition?.jobName ? findRepoContainingPipeline(options, definition.jobName) : [];

  const liveResult = useQuery<AssetNodeDefinitionRunsQuery, AssetNodeDefinitionRunsQueryVariables>(
    ASSET_NODE_DEFINITION_RUNS_QUERY,
    {
      skip: !definition?.jobName,
      variables: {
        repositorySelector: {
          repositoryLocationName: repo?.repositoryLocation.name || '',
          repositoryName: repo?.repository.name || '',
        },
      },
      notifyOnNetworkStatusChange: true,
      pollInterval: 5 * 1000,
    },
  );

  const inProgressRuns =
    liveResult.data?.repositoryOrError.__typename === 'Repository'
      ? liveResult.data.repositoryOrError.inProgressRunsByStep
      : [];

  return (
    <div>
      <div>
        {loading ? (
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
            <Alert
              intent="info"
              title={
                <span>
                  This is a historical view of materializations as of{' '}
                  <span style={{fontWeight: 600}}>
                    <Timestamp
                      timestamp={{ms: Number(params.asOf)}}
                      timeFormat={{showSeconds: true, showTimezone: true}}
                    />
                  </span>
                  .
                </span>
              }
              description={
                <ButtonLink onClick={() => setNavigatedDirectlyToTime(false)} underline="always">
                  {definition
                    ? 'Show definition and latest materializations'
                    : 'Show latest materializations'}
                </ButtonLink>
              }
            />
          </Box>
        ) : definition ? (
          <AssetNodeDefinition assetNode={definition} inProgressRuns={inProgressRuns} />
        ) : undefined}
      </div>
      <AssetMaterializations
        assetKey={assetKey}
        params={params}
        paramsTimeWindowOnly={navigatedDirectlyToTime}
        setParams={setParams}
        inProgressRunIds={
          definition?.opName && inProgressRuns
            ? inProgressRuns.find((f) => f.stepKey === definition.opName)?.runs.map((r) => r.runId)
            : []
        }
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

        definition {
          id
          description
          opName
          jobName

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
