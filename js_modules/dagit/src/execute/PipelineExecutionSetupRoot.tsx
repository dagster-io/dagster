import * as React from "react";
import { Redirect } from "react-router";
import {
  useStorage,
  applyCreateSession,
  IExecutionSession
} from "../LocalStorage";
import * as querystring from "query-string";
import { RouteComponentProps } from "react-router-dom";

export const PipelineExecutionSetupRoot: React.FunctionComponent<RouteComponentProps<{
  pipelinePath: string;
}>> = ({ match }) => {
  const pipelineName = match.params.pipelinePath.split(":")[0];
  const [data, onSave] = useStorage(pipelineName);
  const qs = querystring.parse(window.location.search);

  React.useEffect(() => {
    if (qs.config || qs.mode || qs.solidSelection) {
      const newSession: Partial<IExecutionSession> = {};
      if (typeof qs.config === "string") {
        newSession.runConfigYaml = qs.config;
      }
      if (typeof qs.mode === "string") {
        newSession.mode = qs.mode;
      }
      if (qs.solidSelection instanceof Array) {
        newSession.solidSelection = qs.solidSelection;
      } else if (typeof qs.solidSelection === "string") {
        newSession.solidSelection = [qs.solidSelection];
      }
      if (typeof qs.solidSelectionQuery === "string") {
        newSession.solidSelectionQuery = qs.solidSelectionQuery;
      }

      onSave(applyCreateSession(data, newSession));
    }
  });
  return <Redirect to={{ pathname: `/pipeline/${pipelineName}/playground` }} />;
};
