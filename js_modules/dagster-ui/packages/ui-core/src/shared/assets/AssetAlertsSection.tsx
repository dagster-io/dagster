import {AssetTableDefinitionFragment} from '../../assets/types/AssetTableFragment.types';
import {AssetViewDefinitionNodeFragment} from '../../assets/types/AssetView.types';
import {RepoAddress} from '../../workspace/types';

export const AssetAlertsSection = (_: {
  repoAddress: RepoAddress | null;
  assetNode: AssetViewDefinitionNodeFragment | AssetTableDefinitionFragment;
}) => {
  return null;
};
