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
    if (qs.config || qs.mode || qs.solidSubset) {
      const newSession: Partial<IExecutionSession> = {};
      if (typeof qs.config === "string") {
        newSession.environmentConfigYaml = qs.config;
      }
      if (typeof qs.mode === "string") {
        newSession.mode = qs.mode;
      }
      if (qs.solidSubset instanceof Array) {
        newSession.solidSubset = qs.solidSubset;
      } else if (typeof qs.solidSubset === "string") {
        newSession.solidSubset = [qs.solidSubset];
      }
      if (typeof qs.solidSubsetQuery === "string") {
        newSession.solidSubsetQuery = qs.solidSubsetQuery;
      }

      onSave(applyCreateSession(data, newSession));
    }
  });
  return <Redirect to={{ pathname: `/pipeline/${pipelineName}/playground` }} />;
};
