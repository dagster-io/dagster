import * as querystring from 'query-string';
import * as React from 'react';
import {Redirect} from 'react-router-dom';

import {IExecutionSession, applyCreateSession, useStorage} from '../app/LocalStorage';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {useJobTitle} from '../pipelines/useJobTitle';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  pipelinePath: string;
  repoAddress: RepoAddress;
}

export const PipelineExecutionSetupRoot: React.FC<Props> = (props) => {
  const {pipelinePath, repoAddress} = props;

  const explorerPath = explorerPathFromString(pipelinePath);
  useJobTitle(explorerPath);

  const {pipelineName, pipelineMode} = explorerPath;
  const [data, onSave] = useStorage(
    repoAddress.name,
    `${pipelineName}${pipelineMode ? `:${pipelineMode}` : ''}`,
  );
  const qs = querystring.parse(window.location.search);

  React.useEffect(() => {
    if (qs.config || qs.mode || qs.solidSelection) {
      const newSession: Partial<IExecutionSession> = {};
      if (typeof qs.config === 'string') {
        newSession.runConfigYaml = qs.config;
      }
      if (typeof qs.mode === 'string') {
        newSession.mode = qs.mode;
      }
      if (qs.solidSelection instanceof Array) {
        newSession.solidSelection = qs.solidSelection;
      } else if (typeof qs.solidSelection === 'string') {
        newSession.solidSelection = [qs.solidSelection];
      }
      if (typeof qs.solidSelectionQuery === 'string') {
        newSession.solidSelectionQuery = qs.solidSelectionQuery;
      }

      onSave(applyCreateSession(data, newSession));
    }
  });

  return (
    <Redirect
      to={{
        pathname: workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/playground`),
      }}
    />
  );
};
