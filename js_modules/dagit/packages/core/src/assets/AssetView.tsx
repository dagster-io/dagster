import * as React from 'react';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Group} from '../ui/Group';

import {AssetDetails} from './AssetDetails';
import {AssetMaterializations} from './AssetMaterializations';
import {AssetKey} from './types';

interface Props {
  assetKey: AssetKey;
  asOf: string | null;
}

export const AssetView: React.FC<Props> = ({assetKey, asOf}) => {
  const assetPath = assetKey.path.join(' \u203A ');
  useDocumentTitle(`Asset: ${assetPath}`);

  return (
    <Group spacing={24} direction="column">
      <AssetDetails assetKey={assetKey} asOf={asOf} />
      <AssetMaterializations assetKey={assetKey} asOf={asOf} />
    </Group>
  );
};
