import {AppTopNavRightOfLogo} from '@dagster-io/ui-core/app/AppTopNav/AppTopNavRightOfLogo.oss';
import {FallthroughRoot} from '@dagster-io/ui-core/app/FallthroughRoot.oss';
import {InjectedComponentContext} from '@dagster-io/ui-core/app/InjectedComponentContext';
import {UserPreferences} from '@dagster-io/ui-core/app/UserSettingsDialog/UserPreferences.oss';
import {useAssetGraphExplorerFilters} from '@dagster-io/ui-core/asset-graph/useAssetGraphExplorerFilters.oss';
import {AssetCatalogTableBottomActionBar} from '@dagster-io/ui-core/assets/AssetCatalogTableBottomActionBar.oss';
import {AssetPageHeader} from '@dagster-io/ui-core/assets/AssetPageHeader.oss';
import {AssetsGraphHeader} from '@dagster-io/ui-core/assets/AssetsGraphHeader.oss';
import AssetsOverviewRoot from '@dagster-io/ui-core/assets/AssetsOverviewRoot.oss';
import {useAssetCatalogFiltering} from '@dagster-io/ui-core/assets/useAssetCatalogFiltering.oss';
import {useAssetDefinitionFilterState} from '@dagster-io/ui-core/assets/useAssetDefinitionFilterState.oss';

export const InjectedComponents = ({children}: {children: React.ReactNode}) => {
  return (
    <InjectedComponentContext.Provider
      value={{
        components: {
          AssetPageHeader,
          AppTopNavRightOfLogo,
          UserPreferences,
          AssetsOverview: AssetsOverviewRoot,
          FallthroughRoot,
          AssetsGraphHeader,
          OverviewPageAlerts: null,
          RunMetricsDialog: null,
          AssetCatalogTableBottomActionBar,
        },
        hooks: {
          useAssetDefinitionFilterState,
          useAssetCatalogFiltering,
          useAssetGraphExplorerFilters,
        },
      }}
    >
      {children}
    </InjectedComponentContext.Provider>
  );
};
