import {useQuery} from '@apollo/client';
import {Spinner} from '@dagster-io/ui';
import {gql} from 'graphql.macro';
import {flatten} from 'lodash';
import * as React from 'react';

import {
  GraphExplorer,
  GraphExplorerOptions,
  GRAPH_EXPLORER_ASSET_NODE_FRAGMENT,
  GRAPH_EXPLORER_FRAGMENT,
  GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT,
} from '../pipelines/GraphExplorer';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {InstanceAssetOpsQuery} from './types/InstanceAssetOpsQuery';

export const InstanceAssetOpGraphExplorer: React.FC<{
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  options: GraphExplorerOptions;
  setOptions: (options: GraphExplorerOptions) => void;
}> = (props) => {
  const result = useQuery<InstanceAssetOpsQuery>(INSTANCE_ASSET_OPS_QUERY);

  if (result.data?.repositoriesOrError.__typename !== 'RepositoryConnection') {
    return <Spinner purpose="page" />;
  }

  const repos = result.data.repositoriesOrError.nodes;
  const assetGroupJobs = repos.map((f) => f.assetGroupJob!).filter(Boolean);
  const handles = flatten(assetGroupJobs.map((job) => job.solidHandles));

  return (
    <GraphExplorer
      {...props}
      isGraph={true}
      handles={handles}
      repoAddress={undefined}
      repoAddressForHandle={(handle) => {
        const repo = repos.find((r) =>
          r.assetGroupJob?.solidHandles.some((h) => h.handleID === handle.handleID),
        )!;
        return buildRepoAddress(repo.name, repo.location.name);
      }}
      pipelineOrGraph={assetGroupJobs[0]}
    />
  );
};

const INSTANCE_ASSET_OPS_QUERY = gql`
  query InstanceAssetOpsQuery {
    repositoriesOrError {
      __typename
      ... on RepositoryConnection {
        nodes {
          id
          name
          location {
            id
            name
          }
          assetGroupJob {
            id
            name
            ...GraphExplorerFragment
            solidHandles {
              handleID
              solid {
                name
                definition {
                  assetNodes {
                    id
                    ...GraphExplorerAssetNodeFragment
                  }
                }
              }
              ...GraphExplorerSolidHandleFragment
            }
          }
        }
      }
    }
  }

  ${GRAPH_EXPLORER_FRAGMENT}
  ${GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT}
  ${GRAPH_EXPLORER_ASSET_NODE_FRAGMENT}
`;
