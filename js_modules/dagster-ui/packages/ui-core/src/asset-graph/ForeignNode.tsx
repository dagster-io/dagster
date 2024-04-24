import {Colors, FontFamily, Icon} from '@dagster-io/ui-components';
import {memo} from 'react';
import styled from 'styled-components';

import {ASSET_LINK_NAME_MAX_LENGTH} from './layout';
import {withMiddleTruncation} from '../app/Util';

export const AssetNodeLink = memo(({assetKey}: {assetKey: {path: string[]}}) => {
  const label = assetKey.path[assetKey.path.length - 1]!;
  return (
    <AssetNodeLinkContainer>
      <Icon name="open_in_new" color={Colors.linkDefault()} />
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
  padding: 4px 0 6px 8px;
  margin-top: 6px;
  line-height: 30px;
  font-family: ${FontFamily.monospace};
  color: ${Colors.linkDefault()};
  align-items: center;
  font-weight: 600;
  gap: 4px;
  &:hover .label {
    color: ${Colors.linkDefault()};
    text-decoration: underline;
  }
`;
