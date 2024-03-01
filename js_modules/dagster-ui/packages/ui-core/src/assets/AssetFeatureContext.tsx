import * as React from 'react';

import {AssetEventDetail} from './AssetEventDetail';
import {AssetTabConfig, AssetTabConfigInput, buildAssetTabs} from './AssetTabs';
import {AssetChecksBanner} from './asset-checks/AssetChecksBanner';
import {AssetKey} from './types';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinition.types';
import {
  AssetMaterializationFragment,
  AssetObservationFragment,
} from './types/useRecentAssetEvents.types';
import {AssetKeyInput} from '../graphql/types';

export type AssetViewFeatureInput = {
  selectedTab: string;
  assetKey: AssetKey;
  definition: AssetNodeDefinitionFragment | null;
};

type AssetFeatureContextType = {
  tabBuilder: (input: AssetTabConfigInput) => AssetTabConfig[];
  renderFeatureView: (input: AssetViewFeatureInput) => React.ReactNode;
  AssetChecksBanner: React.ComponentType<{onClose: () => void}>;
  assetEventDetailBuilder: (input: {
    assetKey: AssetKeyInput;
    event: AssetMaterializationFragment | AssetObservationFragment;
    groupName?: string | null;
  }) => React.ReactNode;
};

export const AssetFeatureContext = React.createContext<AssetFeatureContextType>({
  tabBuilder: () => [],
  renderFeatureView: () => <span />,
  AssetChecksBanner: () => <span />,
  assetEventDetailBuilder: (input) => {
    return <AssetEventDetail assetKey={input.assetKey} event={input.event}/>;
  },
});

const renderFeatureView = () => <span />;

export const AssetFeatureProvider = ({children}: {children: React.ReactNode}) => {
  const value = React.useMemo(() => {
    return {
      tabBuilder: buildAssetTabs,
      renderFeatureView,
      AssetChecksBanner,
      assetEventDetailBuilder: () => <span />,
    };
  }, []);

  return <AssetFeatureContext.Provider value={value}>{children}</AssetFeatureContext.Provider>;
};
