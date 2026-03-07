import {useContext} from 'react';

import {AppContext} from './AppContext';

export const usePrefixedCacheKey = (key: string) => {
  const {localCacheIdPrefix} = useContext(AppContext);
  return `${localCacheIdPrefix}/${key}`;
};
