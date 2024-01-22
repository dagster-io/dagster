import {createContext} from 'react';

type InstancePageContextValue = {
  pageTitle: string;
  healthTitle: string;
};

export const InstancePageContext = createContext<InstancePageContextValue>({
  pageTitle: '',
  healthTitle: '',
});
