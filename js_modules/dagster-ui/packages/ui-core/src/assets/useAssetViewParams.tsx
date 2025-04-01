import {AssetViewParams} from './types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

export const decode = ({lineageDepth, showAllEvents, ...rest}: {[key: string]: any}) => {
  const result: AssetViewParams = {...rest};
  if (lineageDepth !== undefined) {
    result.lineageDepth = Number(lineageDepth);
  }
  if (showAllEvents !== undefined) {
    result.showAllEvents =
      showAllEvents === 'true' ? true : showAllEvents === 'false' ? false : undefined;
  }
  return result;
};

export const useAssetViewParams = () => {
  return useQueryPersistedState<AssetViewParams>({decode});
};
