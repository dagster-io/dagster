import {AssetGraphViewType} from './Utils';
import {AssetGraphFetchScope} from './useAssetGraphData';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';

export const getPositionOverrideKey = ({
  viewType,
  explorerPath,
  fetchOptions,
}: {
  viewType: AssetGraphViewType;
  explorerPath: ExplorerPath;
  fetchOptions: AssetGraphFetchScope;
}) => {
  return `asset-graph-position-overrides-${JSON.stringify({
    viewType,
    opsQuery: explorerPath.opsQuery,
    pipelineSelector: fetchOptions.pipelineSelector
      ? {
          pipelineName: fetchOptions.pipelineSelector.pipelineName,
          repositoryName: fetchOptions.pipelineSelector.repositoryName,
          repositoryLocationName: fetchOptions.pipelineSelector.repositoryLocationName,
        }
      : undefined,
    groupSelector: fetchOptions.groupSelector
      ? {
          groupName: fetchOptions.groupSelector.groupName,
          repositoryName: fetchOptions.groupSelector.repositoryName,
          repositoryLocationName: fetchOptions.groupSelector.repositoryLocationName,
        }
      : undefined,
    kinds: fetchOptions.kinds ? [...fetchOptions.kinds].sort() : undefined,
  })}`;
};
