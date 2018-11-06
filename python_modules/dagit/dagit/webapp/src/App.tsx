import * as React from "react";
import gql from "graphql-tag";
import { Query, QueryResult } from "react-apollo";
import { Route, match } from "react-router";
import { BrowserRouter } from "react-router-dom";
import { History } from "history";
import Loading from "./Loading";
import PipelinePage from "./PipelinePage";
import { AppQuery } from "./types/AppQuery";

export default class App extends React.Component {
  public render() {
    return (
      <Query query={APP_QUERY}>
        {(queryResult: QueryResult<AppQuery, any>) => (
          <Loading queryResult={queryResult}>
            {data => {
              return (
                <BrowserRouter>
                  <Route path="/:pipeline/:solid?">
                    {({
                      match,
                      history
                    }: {
                      match: match<{ pipeline: string; solid: string | null }>;
                      history: History;
                    }) => {
                      return (
                        <PipelinePage
                          selectedPipelineName={match && match.params.pipeline}
                          selectedSolidName={match && match.params.solid}
                          history={history}
                          pipelinesOrErrors={data.pipelinesOrErrors}
                        />
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
      ...PipelinePageFragment
    }
  }

  ${PipelinePage.fragments.PipelinePageFragment}
`;
