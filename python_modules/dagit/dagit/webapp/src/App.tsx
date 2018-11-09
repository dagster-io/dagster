import * as React from "react";
import gql from "graphql-tag";
import { Query, QueryResult } from "react-apollo";
import { Route, match, Switch } from "react-router";
import { BrowserRouter } from "react-router-dom";
import { History } from "history";
import Loading from "./Loading";
import PipelinePage from "./PipelinePage";
import ConfigEditor from "./configeditor/ConfigEditor";
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
                  <Switch>
                    <Route
                      path="/:pipeline/config-editor"
                      render={({
                        match,
                        history
                      }: {
                        match: match<{
                          pipeline: string;
                        }>;
                        history: History;
                      }) => {
                        const pipeline = data.pipelinesOrErrors.find(
                          p =>
                            p.__typename === "Pipeline" &&
                            p.name === match.params.pipeline
                        );
                        if (pipeline && pipeline.__typename === "Pipeline") {
                          return (
                            <ConfigEditor
                              pipeline={pipeline}
                              match={match}
                              history={history}
                            />
                          );
                        } else {
                          return null;
                        }
                      }}
                    />
                    <Route
                      path="/:pipeline?/:solid?"
                      render={({
                        match,
                        history
                      }: {
                        match: match<{
                          pipeline: string | null;
                          solid: string | null;
                        }>;
                        history: History;
                      }) => {
                        return (
                          <PipelinePage
                            selectedPipelineName={
                              match && match.params.pipeline
                            }
                            selectedSolidName={match && match.params.solid}
                            history={history}
                            pipelinesOrErrors={data.pipelinesOrErrors}
                          />
                        );
                      }}
                    />
                  </Switch>
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
