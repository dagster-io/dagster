import React, {useContext} from 'react';

// import using type so that the actual file doesn't get bundled into Cloud if it's not imported directly by cloud.
import type {AppTopNavRightOfLogo} from './AppTopNav/AppTopNavRightOfLogo.oss';

type AComponentOrNull<Props> =
  | ((props: Props) => React.ReactNode)
  | React.MemoExoticComponent<(props: Props) => React.ReactNode>
  | null
  | undefined;

export const InjectedComponentContext = React.createContext<{
  AppTopNavRightOfLogo: AComponentOrNull<React.ComponentProps<typeof AppTopNavRightOfLogo>>;
  OverviewPageAlerts?: AComponentOrNull<Record<string, never>>;
}>({
  AppTopNavRightOfLogo: null,
  OverviewPageAlerts: null,
});

export function componentStub(component: keyof React.ContextType<typeof InjectedComponentContext>) {
  return () => {
    const {[component]: Component} = useContext(InjectedComponentContext);
    if (Component) {
      return <Component />;
    }
    return null;
  };
}
