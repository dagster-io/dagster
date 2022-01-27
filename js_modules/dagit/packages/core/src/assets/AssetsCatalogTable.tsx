import * as React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

import {AssetKeysTable} from './AssetKeysTable';
import {AssetNamespaceTable} from './AssetNamespaceTable';
import {AssetViewModeSwitch} from './AssetViewModeSwitch';
import {useAssetView} from './useAssetView';

export const AssetsCatalogTable: React.FC<{prefixPath?: string[]}> = ({prefixPath}) => {
  const [cursor, setCursor] = useQueryPersistedState<string | undefined>({queryKey: 'cursor'});
  const [view, _setView] = useAssetView();
  const history = useHistory();

  useDocumentTitle(
    prefixPath && prefixPath.length ? `Assets: ${prefixPath.join(' \u203A ')}` : 'Assets',
  );
  const setView = (view: 'flat' | 'graph' | 'directory') => {
    if (view === 'graph') {
      history.push('/instance/asset-graph');
      return;
    }
    _setView(view);
    if (view === 'flat' && prefixPath) {
      history.push('/instance/assets');
    } else if (cursor) {
      setCursor(undefined);
    }
  };

  return (
    <Wrapper>
      {view === 'flat' ? (
        <AssetKeysTable
          prefixPath={prefixPath || []}
          switcher={<AssetViewModeSwitch view={view} setView={setView} />}
        />
      ) : (
        <AssetNamespaceTable
          prefixPath={prefixPath || []}
          switcher={<AssetViewModeSwitch view={view} setView={setView} />}
        />
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
