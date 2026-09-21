import {AssetViewDefinitionNodeFragment} from '../../assets/types/AssetView.types';
import {WorkspaceAssetNode} from '../../assets/useAllAssets';
import {RepoAddress} from '../../workspace/types';

export const AssetAlertsSection = (_: {
  repoAddress: RepoAddress | null;
  assetNode: AssetViewDefinitionNodeFragment | WorkspaceAssetNode;
}) => {
  return null;
};
