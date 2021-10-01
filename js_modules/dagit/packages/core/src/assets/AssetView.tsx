import * as React from 'react';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Group} from '../ui/Group';
import {assetKeyToString} from '../workspace/asset-graph/Utils';

import {AssetDetails} from './AssetDetails';
import {AssetMaterializations} from './AssetMaterializations';
import {AssetKey} from './types';

interface Props {
  assetKey: AssetKey;
  asOf: string | null;
}

export const AssetView: React.FC<Props> = ({assetKey, asOf}) => {
  useDocumentTitle(`Asset: ${assetKeyToString(assetKey)}`);

  return (
    <Group spacing={24} direction="column">
      <AssetDetails assetKey={assetKey} asOf={asOf} />
      <AssetMaterializations assetKey={assetKey} asOf={asOf} />
    </Group>
  );
};
