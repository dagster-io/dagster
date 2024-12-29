import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

export function useAssetSelectionState(..._any: any[]) {
  return useQueryPersistedState<string>({
    queryKey: 'asset-selection',
    defaults: {['asset-selection']: ''},
  });
}
