import {Box} from '@dagster-io/ui-components';

import {AssetLink} from '../assets/AssetLink';
type SensorMetadata = {
  assetKeys: {path: string[]}[] | null;
};

export const SensorMonitoredAssets = ({metadata}: {metadata: SensorMetadata | undefined}) => {
  if (!metadata?.assetKeys?.length) {
    return <span />;
  }
  return (
    <Box flex={{direction: 'column', gap: 2}}>
      {metadata.assetKeys.map((key) => (
        <AssetLink key={key.path.join('/')} path={key.path} icon="asset" />
      ))}
    </Box>
  );
};
