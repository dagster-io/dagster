import {ComponentProps} from 'react';

import {GraphQueryInput} from '../ui/GraphQueryInput';

export const AssetGraphAssetSelectionInput = (
  props: Omit<ComponentProps<typeof GraphQueryInput>, 'type'>,
) => {
  return <GraphQueryInput {...props} type="asset_graph" />;
};
