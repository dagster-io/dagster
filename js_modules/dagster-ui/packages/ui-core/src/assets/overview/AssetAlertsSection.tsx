import {Box} from '@dagster-io/ui-components';

import {metadataForAssetNode} from '../AssetMetadata';
import {SectionSkeleton} from './Common';
import {RepoAddress} from '../../workspace/types';
import {AssetNodeDefinitionFragment} from '../types/AssetNodeDefinition.types';

export const AssetAlertsSection = ({
  repoAddress,
  assetNode,
}: {
  repoAddress: RepoAddress | null;
  assetNode: AssetNodeDefinitionFragment | null | undefined;
}) => {
  if (!assetNode) {
    return <SectionSkeleton />;
  }
  const {assetType} = metadataForAssetNode(assetNode);
  const configType = assetNode?.configField?.configType;
  const assetConfigSchema = configType && configType.key !== 'Any' ? configType : null;

  return <Box flex={{direction: 'column', gap: 12}}></Box>;
};
