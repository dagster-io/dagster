import React, {useContext} from 'react';

// import using type so that the actual file doesn't get bundled into Cloud if it's not imported directly by cloud.
import type {AppTopNavRightOfLogo} from './AppTopNav/AppTopNavRightOfLogo.oss';
import type {UserPreferences} from './UserSettingsDialog/UserPreferences.oss';
import AssetsOverviewRoot from '../assets/AssetsOverviewRoot';

type ComponentType = keyof React.JSX.IntrinsicElements | React.JSXElementConstructor<any>;
type AComponentFromComponent<TComponent extends ComponentType> = AComponentWithProps<
  React.ComponentProps<TComponent>
>;

type AComponentWithProps<Props = Record<string, never>> =
  | ((props: Props) => React.ReactNode)
  | React.MemoExoticComponent<(props: Props) => React.ReactNode>;

type InjectedComponentContextType = {
  AppTopNavRightOfLogo: AComponentFromComponent<typeof AppTopNavRightOfLogo> | null;
  OverviewPageAlerts?: AComponentWithProps | null;
  UserPreferences?: AComponentFromComponent<typeof UserPreferences> | null;
  AssetsOverview: AComponentFromComponent<typeof AssetsOverviewRoot> | null;
};
export const InjectedComponentContext = React.createContext<InjectedComponentContextType>({
  AppTopNavRightOfLogo: null,
  OverviewPageAlerts: null,
  AssetsOverview: null,
});

export function componentStub<TComponentKey extends keyof InjectedComponentContextType>(
  component: TComponentKey,
): NonNullable<InjectedComponentContextType[TComponentKey]> {
  return (props: any) => {
    const {[component]: Component} = useContext(InjectedComponentContext);
    if (Component) {
      return <Component {...props} />;
    }
    return null;
  };
}
