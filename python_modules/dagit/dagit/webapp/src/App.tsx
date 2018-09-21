import * as React from "react";
import { Switch, Route } from "react-router";
import { BrowserRouter } from "react-router-dom";
import Page from "./Page";
import PipelinesContainer from "./PipelinesContainer";

export default class App extends React.Component {
  public render() {
    return (
      <Page>
        <BrowserRouter>
          <Route
            path="/:pipeline?"
            render={({ match, history }) => {
              return (
                <PipelinesContainer
                  pipelineName={match.params.pipeline || ""}
                  history={history}
                />
              );
            }}
          />
        </BrowserRouter>
      </Page>
    );
  }
}
