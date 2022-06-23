import {gql, useQuery} from '@apollo/client';
import {Box, Colors, NonIdealState, PageHeader, Tag, Heading} from '@dagster-io/ui';
import React from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RepositoryLink} from '../nav/RepositoryLink';
import {explodeCompositesInHandleGraph} from '../pipelines/CompositeSupport';
import {
  GraphExplorer,
  GraphExplorerOptions,
  GRAPH_EXPLORER_FRAGMENT,
  GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT,
} from '../pipelines/GraphExplorer';
import {explorerPathFromString, explorerPathToString} from '../pipelines/PipelinePathUtils';
import {Loading} from '../ui/Loading';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {RepoAddress} from './types';
import {
  GraphExplorerRootQuery,
  GraphExplorerRootQueryVariables,
} from './types/GraphExplorerRootQuery';

interface Props {
  repoAddress: RepoAddress;
}

export const GraphRoot: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const params = useParams();

  const path = explorerPathFromString(params[0]);

  // Show the name of the composite solid we are within (-1 is the selection, -2 is current parent)
  // or the name of the pipeline tweaked to look a bit more like a graph name.
  const title = path.opNames.length > 1 ? path.opNames[path.opNames.length - 2] : path.pipelineName;
  useDocumentTitle(`Graph: ${title}`);

  return (
    <div style={{height: '100%', display: 'flex', flexDirection: 'column'}}>
      <PageHeader
        title={<Heading>{title}</Heading>}
        tags={
          <Tag icon="schema">
            Graph in <RepositoryLink repoAddress={repoAddress} />
          </Tag>
        }
      />
      <Box
        border={{side: 'top', width: 1, color: Colors.KeylineGray}}
        style={{minHeight: 0, flex: 1, display: 'flex'}}
      >
        <GraphExplorerRoot repoAddress={repoAddress} />
      </Box>
    </div>
  );
};

const GraphExplorerRoot: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const params = useParams();

  const explorerPath = explorerPathFromString(params['0']);
  const history = useHistory();
  const [options, setOptions] = React.useState<GraphExplorerOptions>({
    explodeComposites: false,
    preferAssetRendering: true,
  });

  const parentNames = explorerPath.opNames.slice(0, explorerPath.opNames.length - 1);
  const graphResult = useQuery<GraphExplorerRootQuery, GraphExplorerRootQueryVariables>(
    GRAPH_EXPLORER_ROOT_QUERY,
    {
      variables: {
        graphSelector: {
          repositoryName: repoAddress?.name || '',
          repositoryLocationName: repoAddress?.location || '',
          graphName: explorerPath.pipelineName,
        },
        rootHandleID: parentNames.join('.'),
        requestScopeHandleID: options.explodeComposites ? undefined : parentNames.join('.'),
      },
    },
  );

  return (
    <Loading<GraphExplorerRootQuery> queryResult={graphResult}>
      {({graphOrError: result}) => {
        if (result.__typename === 'GraphNotFoundError') {
          return (
            <NonIdealState icon="error" title="Graph not found" description={result.message} />
          );
        }
        if (result.__typename === 'PythonError') {
          return <NonIdealState icon="error" title="Query Error" description={result.message} />;
        }
        const parentHandle = result.solidHandle;
        const displayedHandles = options.explodeComposites
          ? explodeCompositesInHandleGraph(result.solidHandles)
          : result.solidHandles;

        return (
          <GraphExplorer
            options={options}
            setOptions={setOptions}
            explorerPath={explorerPath}
            onChangeExplorerPath={(path, mode) => {
              const fullPath = workspacePathFromAddress(
                props.repoAddress,
                `/graphs/${explorerPathToString(path)}`,
              );
              if (mode === 'push') {
                history.push(fullPath);
              } else {
                history.replace(fullPath);
              }
            }}
            pipelineOrGraph={result}
            repoAddress={repoAddress}
            handles={displayedHandles}
            parentHandle={parentHandle ? parentHandle : undefined}
            isGraph={true}
            getInvocations={(definitionName) =>
              displayedHandles
                .filter((s) => s.solid.definition.name === definitionName)
                .map((s) => ({handleID: s.handleID}))
            }
          />
        );
      }}
    </Loading>
  );
};

const GRAPH_EXPLORER_ROOT_QUERY = gql`
  query GraphExplorerRootQuery(
    $graphSelector: GraphSelector
    $rootHandleID: String!
    $requestScopeHandleID: String
  ) {
    graphOrError(selector: $graphSelector) {
      ... on Graph {
        id
        name
        ...GraphExplorerFragment

        solidHandle(handleID: $rootHandleID) {
          ...GraphExplorerSolidHandleFragment
        }
        solidHandles(parentHandleID: $requestScopeHandleID) {
          handleID
          solid {
            name
          }
          ...GraphExplorerSolidHandleFragment
        }
      }
      ... on GraphNotFoundError {
        message
      }
      ...PythonErrorFragment
    }
  }
  ${GRAPH_EXPLORER_FRAGMENT}
  ${GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
