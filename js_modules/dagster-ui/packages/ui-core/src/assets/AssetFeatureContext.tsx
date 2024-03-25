import * as React from 'react';

import {AssetTabConfig, AssetTabConfigInput, buildAssetTabs} from './AssetTabs';
import {AssetChecksBanner} from './asset-checks/AssetChecksBanner';
import {AssetKey, AssetViewParams} from './types';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinition.types';
import {GraphData} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';

export type AssetViewFeatureInput = {
  selectedTab: string;
  assetKey: AssetKey;
  definition: AssetNodeDefinitionFragment | null;
};

type AssetFeatureContextType = {
  LineageOptions?: React.ComponentType<{
    assetKey: AssetKeyInput;
    params: AssetViewParams;
    setParams: (params: AssetViewParams) => void;
  }>;
  LineageGraph?: React.ComponentType<{
    params: AssetViewParams;
    assetKey: AssetKeyInput;
    assetGraphData: GraphData;
  }>;

  tabBuilder: (input: AssetTabConfigInput) => AssetTabConfig[];
  renderFeatureView: (input: AssetViewFeatureInput) => React.ReactNode;
  AssetChecksBanner: React.ComponentType<{onClose: () => void}>;
  AssetColumnLinksCell: (input: {column: string | null}) => React.ReactNode;
};

export const AssetFeatureContext = React.createContext<AssetFeatureContextType>({
  tabBuilder: () => [],
  renderFeatureView: () => <span />,
  AssetChecksBanner: () => <span />,
  AssetColumnLinksCell: () => undefined,
  LineageOptions: undefined,
  LineageGraph: undefined,
});

const renderFeatureView = () => <span />;

export const AssetFeatureProvider = ({children}: {children: React.ReactNode}) => {
  const value = React.useMemo(() => {
    return {
      tabBuilder: buildAssetTabs,
      renderFeatureView,
      AssetChecksBanner,
      AssetColumnLinksCell: () => undefined,
      LineageOptions: undefined,
      LineageGraph: undefined,
    };
  }, []);

  return <AssetFeatureContext.Provider value={value}>{children}</AssetFeatureContext.Provider>;
};
