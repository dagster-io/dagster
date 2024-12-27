import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

export function useAssetSelectionState() {
  return useQueryPersistedState<string>({
    queryKey: 'asset-selection',
    defaults: {['asset-selection']: ''},
  });
}
