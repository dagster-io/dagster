import {Colors, Icon, FontFamily} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

import {withMiddleTruncation} from '../app/Util';

import {ASSET_LINK_NAME_MAX_LENGTH} from './layout';

export const AssetNodeLink: React.FC<{
  assetKey: {path: string[]};
}> = React.memo(({assetKey}) => {
  const label = assetKey.path[assetKey.path.length - 1];
  return (
    <AssetNodeLinkContainer>
      <Icon name="open_in_new" color={Colors.Link} />
      <span className="label" title={label}>
        {withMiddleTruncation(label, {
          maxLength: ASSET_LINK_NAME_MAX_LENGTH,
        })}
      </span>
    </AssetNodeLinkContainer>
  );
});

const AssetNodeLinkContainer = styled.div`
  display: flex;
  padding: 4px 8px 6px;
  margin-top: 26px;
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
