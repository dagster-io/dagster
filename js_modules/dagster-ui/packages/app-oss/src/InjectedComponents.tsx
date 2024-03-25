import {AppTopNavRightOfLogo} from '@dagster-io/ui-core/app/AppTopNav/AppTopNavRightOfLogo.oss';
import {InjectedComponentContext} from '@dagster-io/ui-core/app/InjectedComponentContext';
import {UserPreferences} from '@dagster-io/ui-core/app/UserSettingsDialog/UserPreferences.oss';
import AssetsCatalogRoot from '@dagster-io/ui-core/assets/AssetsCatalogRoot';

export const InjectedComponents = ({children}: {children: React.ReactNode}) => {
  return (
    <InjectedComponentContext.Provider
      value={{
        AppTopNavRightOfLogo,
        UserPreferences,
        AssetsOverview: AssetsCatalogRoot,
      }}
    >
      {children}
    </InjectedComponentContext.Provider>
  );
};
