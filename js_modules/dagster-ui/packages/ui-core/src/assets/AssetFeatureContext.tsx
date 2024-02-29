import * as React from 'react';

import {AssetTabConfig, AssetTabConfigInput, buildAssetTabs} from './AssetTabs';
import {AssetChecksBanner} from './asset-checks/AssetChecksBanner';
import {AssetKey} from './types';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinition.types';

export type AssetViewFeatureInput = {
  selectedTab: string;
  assetKey: AssetKey;
  definition: AssetNodeDefinitionFragment | null;
};

type AssetFeatureContextType = {
  tabBuilder: (input: AssetTabConfigInput) => AssetTabConfig[];
  renderFeatureView: (input: AssetViewFeatureInput) => React.ReactNode;
  AssetChecksBanner: React.ComponentType<{onClose: () => void}>;
};

export const AssetFeatureContext = React.createContext<AssetFeatureContextType>({
  tabBuilder: () => [],
  renderFeatureView: () => <span />,
  AssetChecksBanner: () => <span />,
});

const renderFeatureView = () => <span />;

export const AssetFeatureProvider = ({children}: {children: React.ReactNode}) => {
  const value = React.useMemo(() => {
    return {
      tabBuilder: buildAssetTabs,
      renderFeatureView,
      AssetChecksBanner,
    };
  }, []);

  return <AssetFeatureContext.Provider value={value}>{children}</AssetFeatureContext.Provider>;
};
