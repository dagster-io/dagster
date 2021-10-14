import * as React from 'react';

import {useDocumentTitle} from '../hooks/useDocumentTitle';

import {PipelineExplorerPath} from './PipelinePathUtils';

export const useJobTitle = (explorerPath: PipelineExplorerPath, isJob: boolean) => {
  const {pipelineName} = explorerPath;

  const value = React.useMemo(() => {
    if (isJob) {
      return `Job: ${pipelineName}`;
    }
    return `Pipeline: ${pipelineName}`;
  }, [isJob, pipelineName]);

  useDocumentTitle(value);
};
