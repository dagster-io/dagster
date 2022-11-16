import {Colors, Icon, FontFamily} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

import {displayNameForAssetKey} from './Utils';

export const AssetNodeLink: React.FC<{
  assetKey: {path: string[]};
}> = React.memo(({assetKey}) => (
  <AssetNodeLinkContainer>
    <Icon name="open_in_new" color={Colors.Link} />
    <span className="label">{displayNameForAssetKey(assetKey)}</span>
  </AssetNodeLinkContainer>
));

const AssetNodeLinkContainer = styled.div`
  display: flex;
  padding: 4px 8px 6px;
  line-height: 30px;
  font-family: ${FontFamily.monospace};
  color: ${Colors.Link};
  align-items: center;
  font-weight: 600;
  gap: 4px;
  &:hover .label {
    color: ${Colors.Link};
    text-decoration: underline;
  }
`;
