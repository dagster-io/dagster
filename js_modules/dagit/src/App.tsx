import * as React from "react";
import gql from "graphql-tag";
import { Query, QueryResult } from "react-apollo";
import { Route } from "react-router";
import { BrowserRouter } from "react-router-dom";
import Loading from "./Loading";
import PipelinePage from "./PipelinePage";
import { AppQuery } from "./types/AppQuery";

export default class App extends React.Component {
  public render() {
    return (
      <BrowserRouter>
        <Query query={APP_QUERY}>
          {(queryResult: QueryResult<AppQuery, any>) => (
            <Loading queryResult={queryResult}>
              {data => (
                <Route
                  path="/:pipeline?/:tab?"
                  render={({ match, history }) => (
                    <PipelinePage
                      pipelinesOrError={data.pipelinesOrError}
                      history={history}
                      match={match}
                    />
                  )}
                />
              )}
            </Loading>
          )}
        </Query>
      </BrowserRouter>
    );
  }
}

export const APP_QUERY = gql`
  query AppQuery {
    pipelinesOrError {
      ...PipelinePageFragment
    }
  }

  ${PipelinePage.fragments.PipelinePageFragment}
`;
