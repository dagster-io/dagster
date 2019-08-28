import * as React from "react";
import { match, Redirect } from "react-router";
import {
  useStorage,
  applyCreateSession,
  IExecutionSession
} from "../LocalStorage";
import * as querystring from "query-string";

interface PipelineExecutionSetupRootProps {
  match: match<{ pipelineName: string }>;
}

export const PipelineExecutionSetupRoot: React.FunctionComponent<
  PipelineExecutionSetupRootProps
> = ({ match: { params } }) => {
  const [data, onSave] = useStorage({ namespace: params.pipelineName });
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

      onSave(applyCreateSession(data, newSession));
    }
  });
  return <Redirect to={`/execute/${params.pipelineName}`} />;
};
