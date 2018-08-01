import * as React from "react";
import gql from "graphql-tag";
import { Query, QueryResult } from "react-apollo";
import { Route } from "react-router";
import { BrowserRouter } from "react-router-dom";
import Page from "./Page";
import Loading from "./Loading";
import Pipelines from "./Pipelines";
import { AppQuery } from "./types/AppQuery";

class App extends React.Component {
  public render() {
    return (
      <BrowserRouter>
        <Route path="/:pipeline">
          {({ match, history }) => (
            <Query query={APP_QUERY}>
              {(queryResult: QueryResult<AppQuery, any>) => (
                <Page>
                  <Loading queryResult={queryResult}>
                    {(data: AppQuery) => (
                      <Pipelines
                        selectedPipeline={match ? match.params.pipeline : ""}
                        pipelines={data.pipelines}
                        history={history}
                      />
                    )}
                  </Loading>
                </Page>
              )}
            </Query>
          )}
        </Route>
      </BrowserRouter>
    );
  }
}

const APP_QUERY = gql`
  query AppQuery {
    pipelines {
      ...PipelinesFragment
    }
  }

  ${Pipelines.fragments.PipelinesFragment}
`;

export default App;
