import {AppTopNavRightOfLogo} from '@dagster-io/ui-core/app/AppTopNav/AppTopNavRightOfLogo.oss';
import {InjectedComponentContext} from '@dagster-io/ui-core/app/InjectedComponentContext';

export const InjectedComponents = ({children}: {children: React.ReactNode}) => {
  return (
    <InjectedComponentContext.Provider
      value={{
        AppTopNavRightOfLogo,
      }}
    >
      {children}
    </InjectedComponentContext.Provider>
  );
};
