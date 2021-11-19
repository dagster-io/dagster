import * as React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {ButtonGroup} from '../ui/ButtonGroup';

import {AssetKeysTable} from './AssetKeysTable';
import {AssetNamespaceTable} from './AssetNamespaceTable';
import {useAssetView} from './useAssetView';

export const AssetsCatalogTable: React.FC<{prefixPath?: string[]}> = ({prefixPath}) => {
  const [cursor, setCursor] = useQueryPersistedState<string | undefined>({queryKey: 'cursor'});
  const [view, setView] = useAssetView();
  const history = useHistory();
  const isFlattened = view !== 'directory';
  useDocumentTitle(
    prefixPath && prefixPath.length ? `Assets: ${prefixPath.join(' \u203A ')}` : 'Assets',
  );
  const setIsFlattened = (flat: boolean) => {
    setView(flat ? 'flat' : 'directory');
    if (flat && prefixPath) {
      history.push('/instance/assets');
    } else if (cursor) {
      setCursor(undefined);
    }
  };

  const switcher = (
    <ButtonGroup
      activeItems={new Set([view])}
      buttons={[
        {id: 'flat', icon: 'view_list', tooltip: 'List view'},
        {id: 'directory', icon: 'folder', tooltip: 'Folder view'},
      ]}
      onClick={(id) => setIsFlattened(id === 'flat')}
    />
  );

  return (
    <Wrapper>
      {isFlattened ? (
        <AssetKeysTable prefixPath={prefixPath || []} switcher={switcher} />
      ) : (
        <AssetNamespaceTable prefixPath={prefixPath || []} switcher={switcher} />
      )}
    </Wrapper>
  );
};

const Wrapper = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
  position: relative;
  z-index: 0;
`;
