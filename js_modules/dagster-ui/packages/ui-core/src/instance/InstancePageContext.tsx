import * as React from 'react';

type InstancePageContextValue = {
  pageTitle: string;
  healthTitle: string;
};

export const InstancePageContext = React.createContext<InstancePageContextValue>({
  pageTitle: '',
  healthTitle: '',
});
