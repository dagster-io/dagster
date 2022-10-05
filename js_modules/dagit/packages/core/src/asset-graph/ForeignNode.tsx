import {Colors, Icon, FontFamily} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

import {AssetNodeBox, AssetNodeContainer, VersionedBadge} from './AssetNode';
import {displayNameForAssetKey} from './Utils';

export const SourceAssetNode: React.FC<{
  assetKey: {path: string[]};
  backgroundColor?: string;
  selected: boolean;
  versioned?: boolean;
}> = React.memo(({assetKey, backgroundColor, selected, versioned}) => (
  <AssetNodeContainer $selected={selected}>
    <AssetNodeBox $selected={selected}>
      <SourceAssetNodeLink style={{backgroundColor}}>
        <span className="label">{displayNameForAssetKey(assetKey)}</span>
        {versioned ? <VersionedBadge>V</VersionedBadge> : null}
        <VersionedBadge>V</VersionedBadge>
        <Icon name="open_in_new" color={Colors.Gray500} />
      </SourceAssetNodeLink>
    </AssetNodeBox>
  </AssetNodeContainer>
));

const SourceAssetNodeLink = styled.div`
  display: flex;
  padding: 4px 8px 6px;
  line-height: 30px;
  font-family: ${FontFamily.monospace};
  color: ${Colors.Gray500};
  align-items: center;
  font-weight: 600;
  gap: 4px;
  &:hover .label {
    color: ${Colors.Link};
    text-decoration: underline;
  }
`;
