import {gql, useQuery} from '@apollo/client';
import {IconName, NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {Redirect, RouteComponentProps, useHistory} from 'react-router-dom';

import {usePipelineSelector} from 'src/DagsterRepositoryContext';
import {Loading} from 'src/Loading';
import {PipelineExplorer, PipelineExplorerOptions} from 'src/PipelineExplorer';
import {
  PipelineExplorerPath,
  explorerPathFromString,
  explorerPathToString,
} from 'src/PipelinePathUtils';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {
  PipelineExplorerRootQuery,
  PipelineExplorerRootQueryVariables,
  PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot,
} from 'src/types/PipelineExplorerRootQuery';
import {PipelineExplorerSolidHandleFragment} from 'src/types/PipelineExplorerSolidHandleFragment';

function explodeComposite(
  handles: PipelineExplorerSolidHandleFragment[],
  handle: PipelineExplorerSolidHandleFragment,
) {
  if (handle.solid.definition.__typename !== 'CompositeSolidDefinition') {
    throw new Error('explodeComposite takes a composite handle.');
  }

  // Replace all references to this composite's inputs in other solid defitions
  // with the interior target of the input mappings
  handle.solid.definition.inputMappings.forEach((inmap) => {
    const solidName = `${handle.solid.name}.${inmap.mappedInput.solid.name}`;
    handles.forEach((h) =>
      h.solid.outputs.forEach((i) => {
        i.dependedBy.forEach((dep) => {
          if (
            dep.definition.name === inmap.definition.name &&
            dep.solid.name === handle.solid.name
          ) {
            dep.solid.name = solidName;
            dep.definition.name = inmap.mappedInput.definition.name;
          }
        });
      }),
    );
  });

  // Replace all references to this composite's outputs in other solid defitions
  // with the interior target of the output mappings
  handle.solid.definition.outputMappings.forEach((outmap) => {
    const solidName = `${handle.solid.name}.${outmap.mappedOutput.solid.name}`;
    handles.forEach((h) =>
      h.solid.inputs.forEach((i) => {
        i.dependsOn.forEach((dep) => {
          if (
            dep.definition.name === outmap.definition.name &&
            dep.solid.name === handle.solid.name
          ) {
            dep.solid.name = solidName;
            dep.definition.name = outmap.mappedOutput.definition.name;
          }
        });
      }),
    );
  });

  // Find all the solid handles that are within this composite and prefix their
  // names with the composite container's name, giving them names that should
  // match their handleID. (Note: We can't assign them their real handleIDs
  // because we'd have to dig through `handles` to find each solid based on it's
  // name + parentHandleID and then get it's handleID - dependsOn, etc. provide
  // Solid references not SolidHandle references.)
  const nested = handles.filter((h) => h.handleID === `${handle.handleID}.${h.solid.name}`);
  nested.forEach((n) => {
    n.solid.name = n.handleID;
    n.solid.inputs.forEach((i) => {
      i.dependsOn.forEach((d) => {
        d.solid.name = `${handle.handleID}.${d.solid.name}`;
      });
    });
    n.solid.outputs.forEach((i) => {
      i.dependedBy.forEach((d) => {
        d.solid.name = `${handle.handleID}.${d.solid.name}`;
      });
    });
  });

  // Return the interior solids that replace the composite in the graph
  return nested;
}

/**
 * Given a solid handle graph, returns a new solid handle graph with all of the
 * composites recursively replaced with their interior solids. Interior solids
 * are given their handle names ("composite.inner") to avoid name collisions.
 *
 * @param handles All the SolidHandles in the pipeline (NOT just current layer)
 */
function explodeCompositesInHandleGraph(handles: PipelineExplorerSolidHandleFragment[]) {
  // Clone the entire graph so we can modify solid names in-place
  handles = JSON.parse(JSON.stringify(handles));

  // Reset the output to just the solids in the top layer of the graph
  const results = handles.filter((h) => !h.handleID.includes('.'));

  // Find composites in the output and replace the composite with it's content
  // solids (renaming the content solids to include the composite's handle and
  // linking them to the other solids via the composite's input/output mappings)
  while (true) {
    const idx = results.findIndex(
      (h) => h.solid.definition.__typename === 'CompositeSolidDefinition',
    );
    if (idx === -1) {
      break;
    }
    results.splice(idx, 1, ...explodeComposite(handles, results[idx]));
  }

  return results;
}

export const PipelineExplorerRegexRoot: React.FC<RouteComponentProps> = (props) => {
  const explorerPath = explorerPathFromString(props.match.params['0']);
  useDocumentTitle(`Pipeline: ${explorerPath.pipelineName}`);
  return <PipelineExplorerRoot explorerPath={explorerPath} />;
};

export const PipelineExplorerSnapshotRoot: React.FC<RouteComponentProps> = (props) => {
  const explorerPath = explorerPathFromString(props.match.params['0']);
  const {pipelineName, snapshotId} = explorerPath;
  useDocumentTitle(`Snapshot: ${pipelineName}${snapshotId ? `@${snapshotId.slice(0, 8)}` : ''}`);
  return <PipelineExplorerRoot explorerPath={explorerPath} />;
};

const PipelineExplorerRoot: React.FunctionComponent<{explorerPath: PipelineExplorerPath}> = (
  props,
) => {
  const history = useHistory();
  const {explorerPath} = props;
  const [options, setOptions] = React.useState<PipelineExplorerOptions>({
    explodeComposites: false,
  });

  const selectedName = explorerPath.pathSolids[explorerPath.pathSolids.length - 1];

  return (
    <ExplorerSnapshotResolver explorerPath={explorerPath} options={options}>
      {(result) => {
        if (result.__typename === 'NonIdealState') {
          return <NonIdealState {...result} />;
        }
        const parentHandle = result.solidHandle;
        const displayedHandles = options.explodeComposites
          ? explodeCompositesInHandleGraph(result.solidHandles)
          : result.solidHandles;

        const selectedHandle = displayedHandles.find((h) => h.solid.name === selectedName);

        // Run a few assertions on the state of the world and redirect the user
        // back to safety if they've landed in an invalid place. Note that we can
        // pop one layer at a time and this renders recursively until we reach a
        // valid parent.
        const invalidSelection = selectedName && !selectedHandle;
        const invalidParent =
          parentHandle && parentHandle.solid.definition.__typename !== 'CompositeSolidDefinition';

        if (invalidSelection || invalidParent) {
          const n = {...explorerPath};
          n.pathSolids = n.pathSolids.slice(0, n.pathSolids.length - 1);
          return <Redirect to={`/pipeline/${explorerPathToString(n)}`} />;
        }

        return (
          <PipelineExplorer
            options={options}
            setOptions={setOptions}
            explorerPath={explorerPath}
            history={history}
            pipeline={result}
            handles={displayedHandles}
            parentHandle={parentHandle ? parentHandle : undefined}
            selectedHandle={selectedHandle}
            getInvocations={(definitionName) =>
              displayedHandles
                .filter((s) => s.solid.definition.name === definitionName)
                .map((s) => ({handleID: s.handleID}))
            }
          />
        );
      }}
    </ExplorerSnapshotResolver>
  );
};

export const PIPELINE_EXPLORER_ROOT_QUERY = gql`
  query PipelineExplorerRootQuery(
    $pipelineSelector: PipelineSelector
    $snapshotId: String
    $rootHandleID: String!
    $requestScopeHandleID: String
  ) {
    pipelineSnapshotOrError(snapshotId: $snapshotId, activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
        name
        ...PipelineExplorerFragment

        solidHandle(handleID: $rootHandleID) {
          ...PipelineExplorerSolidHandleFragment
        }
        solidHandles(parentHandleID: $requestScopeHandleID) {
          handleID
          solid {
            name
          }
          ...PipelineExplorerSolidHandleFragment
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on PipelineSnapshotNotFoundError {
        message
      }
    }
  }
  ${PipelineExplorer.fragments.PipelineExplorerFragment}
  ${PipelineExplorer.fragments.PipelineExplorerSolidHandleFragment}
`;

interface ResolverProps {
  explorerPath: PipelineExplorerPath;
  options: PipelineExplorerOptions;
  children: (
    result:
      | {
          __typename: 'NonIdealState';
          icon: IconName;
          title: string;
          description?: string;
        }
      | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot,
  ) => React.ReactNode;
}

const ExplorerSnapshotResolver: React.FunctionComponent<ResolverProps> = ({
  children,
  explorerPath,
  options,
}) => {
  const parentNames = explorerPath.pathSolids.slice(0, explorerPath.pathSolids.length - 1);

  const pipelineSelector = usePipelineSelector(explorerPath.pipelineName);
  const queryResult = useQuery<PipelineExplorerRootQuery, PipelineExplorerRootQueryVariables>(
    PIPELINE_EXPLORER_ROOT_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      partialRefetch: true,
      variables: {
        pipelineSelector: explorerPath.snapshotId ? undefined : pipelineSelector,
        snapshotId: explorerPath.snapshotId ? explorerPath.snapshotId : undefined,
        rootHandleID: parentNames.join('.'),
        requestScopeHandleID: options.explodeComposites ? undefined : parentNames.join('.'),
      },
    },
  );
  return (
    <Loading<PipelineExplorerRootQuery> queryResult={queryResult}>
      {({pipelineSnapshotOrError}) => {
        switch (pipelineSnapshotOrError.__typename) {
          case 'PipelineSnapshotNotFoundError':
            return children({
              __typename: 'NonIdealState',
              title: 'Pipeline Snapshot Not Found',
              icon: IconNames.FLOW_BRANCH,
              description: pipelineSnapshotOrError.message,
            });
          case 'PipelineNotFoundError':
            return children({
              __typename: 'NonIdealState',
              title: 'Pipeline Not Found',
              icon: IconNames.FLOW_BRANCH,
              description: pipelineSnapshotOrError.message,
            });
          case 'PythonError':
            return children({
              __typename: 'NonIdealState',
              title: 'Query Error',
              icon: IconNames.ERROR,
            });
          default:
            return children(pipelineSnapshotOrError);
        }
      }}
    </Loading>
  );
};
