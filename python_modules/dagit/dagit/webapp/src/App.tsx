import * as React from "react";
import gql from "graphql-tag";
import { Query, QueryResult } from "react-apollo";
import { Route } from "react-router";
import { BrowserRouter } from "react-router-dom";
import Loading from "./Loading";
import PipelineExplorer from "./PipelineExplorer";
import PipelineJumpBar from "./PipelineJumpBar";
import PythonErrorInfo from "./PythonErrorInfo";
import { AppQuery } from "./types/AppQuery";

import { Alignment, Navbar, NonIdealState } from "@blueprintjs/core";
import navBarImage from "./images/nav-logo.png";

export default class App extends React.Component {
  public render() {
    return (
      <Query query={APP_QUERY}>
        {(queryResult: QueryResult<AppQuery, any>) => (
          <Loading queryResult={queryResult}>
            {data => (
              <BrowserRouter>
                <Route path="/:pipeline/:solid?">
                  {({ match, history }) => {
                    const selectedPipeline = data.pipelines.find(
                      p => (match ? p.name === match.params.pipeline : false)
                    );
                    const selectedSolid =
                      selectedPipeline &&
                      selectedPipeline.solids.find(
                        s => (match ? s.name === match.params.solid : false)
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
                              pipelines={data.pipelines}
                              history={history}
                            />
                          </Navbar.Group>
                        </Navbar>
                        {data.error ? (
                          <PythonErrorInfo error={data.error} />
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
            )}
          </Loading>
        )}
      </Query>
    );
  }
}

export const APP_QUERY = gql`
  query AppQuery {
    error
    pipelines {
      ...PipelineFragment
    }
  }

  ${PipelineExplorer.fragments.PipelineFragment}
`;
