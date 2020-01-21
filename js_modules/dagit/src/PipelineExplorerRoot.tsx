import * as React from "react";
import { match } from "react-router";
import gql from "graphql-tag";
import { History } from "history";
import { useQuery } from "react-apollo";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";

import Loading from "./Loading";
import PipelineExplorer from "./PipelineExplorer";
import {
  PipelineExplorerRootQuery,
  PipelineExplorerRootQueryVariables
} from "./types/PipelineExplorerRootQuery";
import { PipelineExplorerParentSolidHandleFragment } from "./types/PipelineExplorerParentSolidHandleFragment";

interface IPipelineExplorerRootProps {
  location: { pathname: string };
  match: match<{ 0: string }>;
  history: History<any>;
}

function flattenHandleGraph(
  handles: PipelineExplorerParentSolidHandleFragment[]
) {
  handles = JSON.parse(JSON.stringify(handles));
  const results = handles.filter(h => !h.handleID.includes("."));

  let found = true;
  while (found) {
    found = false;
    for (let ii = results.length - 1; ii--; ii >= 0) {
      const handle = results[ii];
      if (handle.solid.definition.__typename === "CompositeSolidDefinition") {
        handle.solid.definition.inputMappings.forEach(inmap => {
          const solidName = `${handle.solid.name}.${inmap.mappedInput.solid.name}`;
          // find people consuming this output with name definition.name
          handles.forEach(h =>
            h.solid.outputs.forEach(i => {
              i.dependedBy.forEach(dep => {
                if (
                  dep.definition.name === inmap.definition.name &&
                  dep.solid.name === handle.solid.name
                ) {
                  dep.solid.name = solidName;
                  dep.definition.name = inmap.mappedInput.definition.name;
                }
              });
            })
          );
        });
        handle.solid.definition.outputMappings.forEach(outmap => {
          const solidName = `${handle.solid.name}.${outmap.mappedOutput.solid.name}`;
          // find people consuming this output with name definition.name
          handles.forEach(h =>
            h.solid.inputs.forEach(i => {
              i.dependsOn.forEach(dep => {
                if (
                  dep.definition.name === outmap.definition.name &&
                  dep.solid.name === handle.solid.name
                ) {
                  dep.solid.name = solidName;
                  dep.definition.name = outmap.mappedOutput.definition.name;
                }
              });
            })
          );
        });

        const nested = handles.filter(
          h => h.handleID === `${handle.handleID}.${h.solid.name}`
        );
        console.log(
          `Found ${handle.handleID} with children: ${nested.map(
            n => n.solid.name
          )}`
        );
        nested.forEach(n => {
          n.solid.name = `${handle.handleID}.${n.solid.name}`;
          n.solid.inputs.forEach(i => {
            i.dependsOn.forEach(d => {
              d.solid.name = `${handle.handleID}.${d.solid.name}`;
            });
          });
          n.solid.outputs.forEach(i => {
            i.dependedBy.forEach(d => {
              d.solid.name = `${handle.handleID}.${d.solid.name}`;
            });
          });
        });
        results.splice(ii, 1, ...nested);
        found = true;
        break;
      }
    }
  }
  return results;
}

const PipelineExplorerRoot: React.FunctionComponent<IPipelineExplorerRootProps> = props => {
  const [pipelineSelector, ...pathSolids] = props.match.params["0"].split("/");
  const [pipelineName, query] = [...pipelineSelector.split(":"), ""];

  const parentNames = pathSolids.slice(0, pathSolids.length - 1);
  const selectedName = pathSolids[pathSolids.length - 1];

  const flattenComposites = true;

  const queryResult = useQuery<
    PipelineExplorerRootQuery,
    PipelineExplorerRootQueryVariables
  >(PIPELINE_EXPLORER_ROOT_QUERY, {
    fetchPolicy: "cache-and-network",
    partialRefetch: true,
    variables: Object.assign(
      {
        pipeline: pipelineName,
        rootHandleID: parentNames.join(".")
      },
      flattenComposites
        ? {}
        : {
            requestScopeHandleID: parentNames.join(".")
          }
    )
  });

  return (
    <Loading<PipelineExplorerRootQuery> queryResult={queryResult}>
      {({ pipelineOrError }) => {
        switch (pipelineOrError.__typename) {
          case "PipelineNotFoundError":
            return (
              <NonIdealState
                icon={IconNames.FLOW_BRANCH}
                title="Pipeline Not Found"
                description={pipelineOrError.message}
              />
            );
          case "InvalidSubsetError":
          case "PythonError":
            return <NonIdealState icon={IconNames.ERROR} title="Query Error" />;
          default:
            const pipeline = pipelineOrError;
            let displayedHandles = pipeline.solidHandles;
            const parentSolidHandle = pipelineOrError.solidHandle;

            if (flattenComposites) {
              displayedHandles = flattenHandleGraph(pipeline.solidHandles);
            }

            return (
              <PipelineExplorer
                history={props.history}
                path={pathSolids}
                visibleSolidsQuery={query}
                pipeline={pipelineOrError}
                handles={displayedHandles}
                flattenComposites={true}
                parentHandle={parentSolidHandle ? parentSolidHandle : undefined}
                selectedHandle={displayedHandles.find(
                  h => h.solid.name === selectedName
                )}
                getInvocations={definitionName =>
                  displayedHandles
                    .filter(s => s.solid.definition.name === definitionName)
                    .map(s => ({ handleID: s.handleID }))
                }
              />
            );
        }
      }}
    </Loading>
  );
};

export const PIPELINE_EXPLORER_ROOT_QUERY = gql`
  query PipelineExplorerRootQuery(
    $pipeline: String!
    $rootHandleID: String!
    $requestScopeHandleID: String
  ) {
    pipelineOrError(params: { name: $pipeline }) {
      ... on PipelineReference {
        name
      }
      ... on Pipeline {
        ...PipelineExplorerFragment

        solidHandle(handleID: $rootHandleID) {
          ...PipelineExplorerParentSolidHandleFragment
        }
        solidHandles(parentHandleID: $requestScopeHandleID) {
          handleID
          solid {
            name
          }
          ...PipelineExplorerSolidHandleFragment
          ...PipelineExplorerParentSolidHandleFragment
        }
      }
      ... on PipelineNotFoundError {
        message
      }
    }
  }
  ${PipelineExplorer.fragments.PipelineExplorerFragment}
  ${PipelineExplorer.fragments.PipelineExplorerSolidHandleFragment}
  ${PipelineExplorer.fragments.PipelineExplorerParentSolidHandleFragment}
`;

export default PipelineExplorerRoot;
