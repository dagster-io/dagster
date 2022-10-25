import type {MetadataTableRow} from '@dagster-io/ui';
import React from 'react';

type FeatureGatesContextValue = {
  ExtraFeatureGates: Array<MetadataTableRow>;
};

export const FeatureGateContext = React.createContext<FeatureGatesContextValue>({
  ExtraFeatureGates: [],
});
