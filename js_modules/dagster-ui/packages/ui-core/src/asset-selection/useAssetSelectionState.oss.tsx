import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

export function getAssetSelectionQueryString(search: string = location.search) {
  const params = new URLSearchParams(search);
  return params.get('asset-selection') ?? undefined;
}
export function useAssetSelectionState() {
  return useQueryPersistedState<string>({
    queryKey: 'asset-selection',
    defaults: {['asset-selection']: ''},
    behavior: 'push',
  });
}
