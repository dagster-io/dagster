import React from 'react';

type FeatureGatesContextValue = {
  ExtraFeatureGates?: React.ReactNode;
};

export const FeatureGateContext = React.createContext<FeatureGatesContextValue>({
  ExtraFeatureGates: undefined,
});
