import React, {useContext} from 'react';

// import using type so that the actual file doesn't get bundled into Cloud if it's not imported directly by cloud.
import type {AppTopNavRightOfLogo} from './AppTopNav/AppTopNavRightOfLogo.oss';
import {FallthroughRoot} from './FallthroughRoot.oss';
import type {UserPreferences} from './UserSettingsDialog/UserPreferences.oss';
import {assertUnreachable} from './Util';
import {useAssetGraphExplorerFilters} from '../asset-graph/useAssetGraphExplorerFilters.oss';
import {AssetCatalogTableBottomActionBar} from '../assets/AssetCatalogTableBottomActionBar.oss';
import {AssetPageHeader} from '../assets/AssetPageHeader.oss';
import {AssetsGraphHeader} from '../assets/AssetsGraphHeader.oss';
import AssetsOverviewRoot from '../assets/AssetsOverviewRoot.oss';
import {useAssetCatalogFiltering} from '../assets/useAssetCatalogFiltering.oss';
import {useAssetDefinitionFilterState} from '../assets/useAssetDefinitionFilterState.oss';

type ComponentType = keyof React.JSX.IntrinsicElements | React.JSXElementConstructor<any>;
type AComponentFromComponent<TComponent extends ComponentType> = AComponentWithProps<
  React.ComponentProps<TComponent>
>;

type AComponentWithProps<Props = Record<string, never>> =
  | ((props: Props) => React.ReactNode)
  | React.MemoExoticComponent<(props: Props) => React.ReactNode>;

type InjectedComponentContextType = {
  AppTopNavRightOfLogo: AComponentFromComponent<typeof AppTopNavRightOfLogo> | null;
  OverviewPageAlerts: AComponentWithProps | null;
  UserPreferences: AComponentFromComponent<typeof UserPreferences> | null;
  AssetsOverview: AComponentFromComponent<typeof AssetsOverviewRoot> | null;
  FallthroughRoot: AComponentFromComponent<typeof FallthroughRoot> | null;
  AssetsGraphHeader: AComponentFromComponent<typeof AssetsGraphHeader> | null;

  RunMetricsDialog: AComponentWithProps<{
    runId: string;
    isOpen: boolean;
    onClose: () => void;
  }> | null;
  AssetPageHeader: AComponentFromComponent<typeof AssetPageHeader>;
  AssetCatalogTableBottomActionBar: AComponentFromComponent<
    typeof AssetCatalogTableBottomActionBar
  >;
};

type InjectedHookContextType = {
  useAssetDefinitionFilterState: typeof useAssetDefinitionFilterState;
  useAssetCatalogFiltering: typeof useAssetCatalogFiltering;
  useAssetGraphExplorerFilters: typeof useAssetGraphExplorerFilters;
};
export const InjectedComponentContext = React.createContext<{
  components: InjectedComponentContextType;
  hooks: InjectedHookContextType;
}>({components: {} as any, hooks: {} as any});

export function componentStub<TComponentKey extends keyof InjectedComponentContextType>(
  componentName: TComponentKey,
): NonNullable<InjectedComponentContextType[TComponentKey]> {
  return (props: any) => {
    const {
      components: {[componentName]: Component},
    } = useContext(InjectedComponentContext);
    if (Component) {
      return <Component {...props} />;
    }
    return null;
  };
}

export function hookStub<TFunctionKey extends keyof InjectedHookContextType>(
  hookName: TFunctionKey,
): InjectedHookContextType[TFunctionKey] {
  return function useHookStub(...args: Parameters<InjectedHookContextType[TFunctionKey]>) {
    const {
      hooks: {[hookName]: hook},
    } = useContext(InjectedComponentContext);

    if (!hook) {
      assertUnreachable(hook);
    }

    // @ts-expect-error - "A spread argument must either have a tuple type or be passed to a rest parameter.ts", not sure why we get this error
    return hook(...args);
  } as InjectedHookContextType[TFunctionKey];
}
