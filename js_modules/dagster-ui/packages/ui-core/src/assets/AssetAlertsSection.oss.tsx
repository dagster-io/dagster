import {RepoAddress} from '../workspace/types';
import {AssetTableDefinitionFragment} from './types/AssetTableFragment.types';
import {AssetViewDefinitionNodeFragment} from './types/AssetView.types';

export const AssetAlertsSection = (_: {
  repoAddress: RepoAddress | null;
  assetNode: AssetViewDefinitionNodeFragment | AssetTableDefinitionFragment;
}) => {
  return null;
};
