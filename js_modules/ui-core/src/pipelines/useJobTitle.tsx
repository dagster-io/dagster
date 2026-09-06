import {useMemo} from 'react';

import {ExplorerPath} from './PipelinePathUtils';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

export const useJobTitle = (explorerPath: ExplorerPath, isJob: boolean, section?: string) => {
  const {pipelineName} = explorerPath;

  const value = useMemo(() => {
    const root = isJob ? 'Jobs' : 'Pipelines';
    const base = `${root} | ${pipelineName}`;
    return section ? `${base} | ${section}` : base;
  }, [isJob, pipelineName, section]);

  useDocumentTitle(value);
};
