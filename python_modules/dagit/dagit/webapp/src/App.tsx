import * as React from "react";
import gql from "graphql-tag";
import { Query, QueryResult } from "react-apollo";
import { Route } from "react-router";
import { BrowserRouter } from "react-router-dom";
import Loading from "./Loading";
import Pipelines from "./Pipelines";
import PipelinesNav from "./PipelinesNav";
import { AppQuery } from "./types/AppQuery";

import { Alignment, Navbar } from "@blueprintjs/core";
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
                  {({ match, history }) => (
                    <div>
                      <Navbar>
                        <Navbar.Group align={Alignment.LEFT}>
                          <Navbar.Heading>
                            <img src={navBarImage} style={{ height: 34 }} />
                          </Navbar.Heading>
                          <Navbar.Divider />
                          <PipelinesNav
                            selectedPipeline={
                              match ? match.params.pipeline : ""
                            }
                            selectedSolid={match ? match.params.solid : ""}
                            pipelines={data.pipelines}
                            history={history}
                          />
                        </Navbar.Group>
                      </Navbar>
                      <Pipelines
                        selectedPipeline={match ? match.params.pipeline : ""}
                        selectedSolid={match ? match.params.solid : ""}
                        pipelines={data.pipelines}
                        history={history}
                      />
                    </div>
                  )}
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
    pipelines {
      ...PipelinesFragment
    }
  }

  ${Pipelines.fragments.PipelinesFragment}
`;
