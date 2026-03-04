import {Box} from '@dagster-io/ui-components';

import {AssetLink} from '../assets/AssetLink';
// eslint-disable-next-line no-restricted-imports
import {SensorMetadata} from '../graphql/types-do-not-use';

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
