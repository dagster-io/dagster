import {ColorsWIP, IconWIP, FontFamily} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

import {displayNameForAssetKey} from '../../app/Util';

export const ForeignNode: React.FC<{assetKey: {path: string[]}}> = React.memo(({assetKey}) => (
  <ForeignNodeLink>
    <span className="label">{displayNameForAssetKey(assetKey)}</span>
    <IconWIP name="open_in_new" color={ColorsWIP.Gray500} />
  </ForeignNodeLink>
));

const ForeignNodeLink = styled.div`
  display: flex;
  padding: 4px 8px 6px;
  line-height: 30px;
  font-family: ${FontFamily.monospace};
  color: ${ColorsWIP.Gray500};
  align-items: center;
  font-weight: 600;
  gap: 4px;
  &:hover .label {
    color: ${ColorsWIP.Link};
    text-decoration: underline;
  }
`;
export const getForeignNodeDimensions = (id: string) => {
  const path = JSON.parse(id);
  return {width: displayNameForAssetKey({path}).length * 7 + 30, height: 30};
};
