import {RepoAddress} from '../workspace/types';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinition.types';

export const AssetAlertsSection = (_: {
  repoAddress: RepoAddress | null;
  assetNode: AssetNodeDefinitionFragment | null | undefined;
}) => {
  return null;
};
