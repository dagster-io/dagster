import qs from 'qs';

import {AssetViewParams, AssetViewTab} from './types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

export const decode = ({lineageDepth, showAllEvents, view, ...rest}: qs.ParsedQs) => {
  const result: AssetViewParams = {...rest};
  if (typeof view === 'string') {
    result.view = view as AssetViewTab;
  }
  if (typeof lineageDepth === 'string') {
    result.lineageDepth = Number(lineageDepth);
  }
  if (typeof showAllEvents === 'string') {
    result.showAllEvents =
      showAllEvents === 'true' ? true : showAllEvents === 'false' ? false : undefined;
  }
  return result;
};

export const useAssetViewParams = () => {
  return useQueryPersistedState<AssetViewParams>({decode});
};
