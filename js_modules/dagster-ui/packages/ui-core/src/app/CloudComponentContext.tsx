import React, {useContext} from 'react';

import {AppTopNavRightOfLogo} from './AppTopNav/AppTopNavRightOfLogo.oss';

export const CloudComponentContext = React.createContext<{
  AppTopNavRightOfLogo: (() => React.ReactNode) | React.MemoExoticComponent<() => React.ReactNode>;
}>({
  AppTopNavRightOfLogo,
});

export const componentStub = (component: keyof React.ContextType<typeof CloudComponentContext>) => {
  return () => {
    const {[component]: Component} = useContext(CloudComponentContext);
    return <Component />;
  };
};
