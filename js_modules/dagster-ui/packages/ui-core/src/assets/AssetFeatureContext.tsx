import * as React from 'react';

import {AssetTabConfig, AssetTabConfigInput, useAssetTabs} from './AssetTabs';
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

  useTabBuilder: (input: AssetTabConfigInput) => AssetTabConfig[];
  renderFeatureView: (input: AssetViewFeatureInput) => React.ReactNode;
  AssetColumnLinksCell: (input: {column: string | null}) => React.ReactNode;

  enableAssetHealthOverviewPreview: boolean;
};

export const AssetFeatureContext = React.createContext<AssetFeatureContextType>({
  useTabBuilder: () => [],
  renderFeatureView: () => <span />,
  AssetColumnLinksCell: () => undefined,
  LineageOptions: undefined,
  LineageGraph: undefined,
  enableAssetHealthOverviewPreview: false,
});

const renderFeatureView = () => <span />;

export const AssetFeatureProvider = ({children}: {children: React.ReactNode}) => {
  const value = React.useMemo(() => {
    return {
      useTabBuilder: useAssetTabs,
      renderFeatureView,
      AssetColumnLinksCell: () => undefined,
      LineageOptions: undefined,
      LineageGraph: undefined,
      enableAssetHealthOverviewPreview: false,
    };
  }, []);

  return <AssetFeatureContext.Provider value={value}>{children}</AssetFeatureContext.Provider>;
};
