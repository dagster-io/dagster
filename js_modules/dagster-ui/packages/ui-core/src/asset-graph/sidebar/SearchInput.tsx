import {Box} from '@dagster-io/ui-components';
import * as React from 'react';

import {AssetKey} from '../../assets/types';
import {SearchFilter} from '../sidebar/SearchFilter';

interface SearchInputProps {
  allAssetKeys: AssetKey[];
  selectNode: (
    e: React.MouseEvent<any> | React.KeyboardEvent<any>,
    nodeId: string,
    sidebarNodeInfo?: {path: string; direction: 'root-to-leaf' | 'leaf-to-root'},
  ) => void;
}

export const SearchInput = ({allAssetKeys, selectNode}: SearchInputProps) => {
  const searchValues = React.useMemo(() => {
    return allAssetKeys.map((key) => ({
      value: JSON.stringify(key.path),
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      label: key.path[key.path.length - 1]!,
    }));
  }, [allAssetKeys]);

  return (
    <Box padding={{vertical: 8, horizontal: 12}}>
      <SearchFilter values={searchValues} onSelectValue={selectNode} />
    </Box>
  );
};
