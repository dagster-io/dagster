import * as querystring from 'query-string';
import * as React from 'react';
import {Redirect} from 'react-router';
import {RouteComponentProps} from 'react-router-dom';

import {useRepositorySelector} from 'src/DagsterRepositoryContext';
import {IExecutionSession, applyCreateSession, useStorage} from 'src/LocalStorage';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';

export const PipelineExecutionSetupRoot: React.FunctionComponent<RouteComponentProps<{
  pipelinePath: string;
}>> = ({match}) => {
  const {repositoryName} = useRepositorySelector();
  const pipelineName = match.params.pipelinePath.split(':')[0];
  useDocumentTitle(`Pipeline: ${pipelineName}`);

  const [data, onSave] = useStorage(repositoryName, pipelineName);
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
  return <Redirect to={{pathname: `/pipeline/${pipelineName}/playground`}} />;
};
