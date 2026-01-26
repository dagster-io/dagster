import {createContext, useContext} from 'react';

import {IRunFailureEvent} from './RunMetadataProvider';

interface RunFailureInfoContextType {
  failureInfo: IRunFailureEvent | null;
  setFailureInfo: (info: IRunFailureEvent | null) => void;
}

export const RunFailureInfoContext = createContext<RunFailureInfoContextType>({
  failureInfo: null,
  setFailureInfo: () => {},
});

export const useRunFailureInfo = () => useContext(RunFailureInfoContext);
