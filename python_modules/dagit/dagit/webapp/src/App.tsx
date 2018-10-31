import * as React from "react";
import gql from "graphql-tag";
import { Query, QueryResult } from "react-apollo";
import { Route } from "react-router";
import { BrowserRouter } from "react-router-dom";
import Loading from "./Loading";
import PipelineExplorer from "./PipelineExplorer";
import PipelineJumpBar from "./PipelineJumpBar";
import PythonErrorInfo from "./PythonErrorInfo";
import {
  AppQuery,
  AppQuery_pipelinesOrErrors,
  AppQuery_pipelinesOrErrors_Pipeline
} from "./types/AppQuery";

import { Alignment, Navbar, NonIdealState } from "@blueprintjs/core";
import navBarImage from "./images/nav-logo.png";

function isPipeline(
  item: AppQuery_pipelinesOrErrors
): item is AppQuery_pipelinesOrErrors_Pipeline {
  return (item as AppQuery_pipelinesOrErrors_Pipeline).solids !== undefined;
}

export default class App extends React.Component {
  public render() {
    return (
      <Query query={APP_QUERY}>
        {(queryResult: QueryResult<AppQuery, any>) => (
          <Loading queryResult={queryResult}>
            {data => {
              const first = data.pipelinesOrErrors[0];
              const pipelines = data.pipelinesOrErrors.filter(isPipeline);

              return (
                <BrowserRouter>
                  <Route path="/:pipeline/:solid?">
                    {({ match, history }) => {
                      const selectedPipeline =
                        match &&
                        pipelines.find(p => p.name === match.params.pipeline);
                      const selectedSolid =
                        selectedPipeline &&
                        selectedPipeline.solids.find(
                          s => s.name === match.params.solid
                        );

                      return (
                        <>
                          <Navbar>
                            <Navbar.Group align={Alignment.LEFT}>
                              <Navbar.Heading>
                                <img src={navBarImage} style={{ height: 34 }} />
                              </Navbar.Heading>
                              <Navbar.Divider />
                              <PipelineJumpBar
                                selectedPipeline={selectedPipeline}
                                selectedSolid={selectedSolid}
                                pipelines={pipelines}
                                history={history}
                              />
                            </Navbar.Group>
                          </Navbar>
                          {!isPipeline(first) ? (
                            <PythonErrorInfo error={first} />
                          ) : selectedPipeline ? (
                            <PipelineExplorer
                              pipeline={selectedPipeline}
                              solid={selectedSolid}
                              history={history}
                            />
                          ) : (
                            <NonIdealState
                              title="No pipeline selected"
                              description="Select a pipeline in the sidebar on the left"
                            />
                          )}
                        </>
                      );
                    }}
                  </Route>
                </BrowserRouter>
              );
            }}
          </Loading>
        )}
      </Query>
    );
  }
}

export const APP_QUERY = gql`
  query AppQuery {
    pipelinesOrErrors {
      ... on Error {
        message
        stack
      }
      ... on Pipeline {
        ...PipelineFragment
      }
    }
  }

  ${PipelineExplorer.fragments.PipelineFragment}
`;
