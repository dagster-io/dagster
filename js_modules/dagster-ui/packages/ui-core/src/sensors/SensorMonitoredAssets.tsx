import {Box} from '@dagster-io/ui-components';

import {AssetLink} from '../assets/AssetLink';
import {SensorMetadata} from '../graphql/types';

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
