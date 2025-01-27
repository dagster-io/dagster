import {RepoAddress} from '../workspace/types';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinition.types';
import {AssetTableDefinitionFragment} from './types/AssetTableFragment.types';

export const AssetAlertsSection = (_: {
  repoAddress: RepoAddress | null;
  assetNode: AssetNodeDefinitionFragment | AssetTableDefinitionFragment;
}) => {
  return null;
};
