import * as React from "react";
import gql from "graphql-tag";
import { Query, QueryResult } from "react-apollo";
import { Route, Switch } from "react-router";
import { BrowserRouter } from "react-router-dom";
import { History } from "history";
import Loading from "./Loading";
import PipelinePage, { IPipelinePageMatch } from "./PipelinePage";
import { AppQuery } from "./types/AppQuery";

export default class App extends React.Component {
  public render() {
    return (
      <Query query={APP_QUERY}>
        {(queryResult: QueryResult<AppQuery, any>) => (
          <Loading queryResult={queryResult}>
            {data => (
              <BrowserRouter>
                <Switch>
                  <Route
                    path="/:pipeline?/:tab?"
                    render={({
                      match,
                      history
                    }: {
                      match: IPipelinePageMatch;
                      history: History;
                    }) => (
                      <PipelinePage
                        pipelinesOrErrors={data.pipelinesOrErrors}
                        history={history}
                        match={match}
                      />
                    )}
                  />
                  />
                </Switch>
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
    pipelinesOrErrors {
      ...PipelinePageFragment
    }
  }

  ${PipelinePage.fragments.PipelinePageFragment}
`;
