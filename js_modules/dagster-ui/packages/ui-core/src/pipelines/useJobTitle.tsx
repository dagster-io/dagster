import {useMemo} from 'react';

import {ExplorerPath} from './PipelinePathUtils';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

export const useJobTitle = (explorerPath: ExplorerPath, isJob: boolean) => {
  const {pipelineName} = explorerPath;

  const value = useMemo(() => {
    if (isJob) {
      return `Job: ${pipelineName}`;
    }
    return `Pipeline: ${pipelineName}`;
  }, [isJob, pipelineName]);

  useDocumentTitle(value);
};
