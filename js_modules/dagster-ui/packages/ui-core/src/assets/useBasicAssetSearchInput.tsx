import {TextInput} from '@dagster-io/ui-components';

import {AssetTableFragment} from './types/AssetTableFragment.types';
import {useAssetSearch} from './useAssetSearch';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {FilterableAssetDefinition} from './useAssetDefinitionFilterState.oss';

export const useBasicAssetSearchInput = <T extends {
  id: string;
  key: {path: Array<string>};
  definition?: FilterableAssetDefinition | null;
},>(
  assets: T[],
  prefixPath: string[] = [],
) => {
  const [search, setSearch] = useQueryPersistedState<string | undefined>({queryKey: 'q'});

  const searchPath = (search || '')
    .replace(/(( ?> ?)|\.|\/)/g, '/')
    .toLowerCase()
    .trim();

  const filterInput = (
    <TextInput
      value={search || ''}
      style={{width: '30vw', minWidth: 150, maxWidth: 400}}
      placeholder={
        prefixPath.length ? `Filter asset keys in ${prefixPath.join('/')}…` : `Filter asset keys…`
      }
      onChange={(e: React.ChangeEvent<any>) => setSearch(e.target.value)}
    />
  );

  const filtered = useAssetSearch(searchPath, assets);

  return {filterInput, filtered, searchPath};
};
