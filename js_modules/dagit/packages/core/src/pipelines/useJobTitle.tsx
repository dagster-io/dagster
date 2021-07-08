import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

import {PipelineExplorerPath} from './PipelinePathUtils';

export const useJobTitle = (explorerPath: PipelineExplorerPath) => {
  const {flagPipelineModeTuples} = useFeatureFlags();
  const {pipelineName, pipelineMode} = explorerPath;

  const value = React.useMemo(() => {
    if (flagPipelineModeTuples) {
      return `Job: ${pipelineName}${pipelineMode === 'default' ? '' : `:${pipelineMode}`}`;
    }
    return `Pipeline: ${pipelineName}`;
  }, [flagPipelineModeTuples, pipelineMode, pipelineName]);

  useDocumentTitle(value);
};
