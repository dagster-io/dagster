import React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from '../../ui/Colors';
import {IconWIP} from '../../ui/Icon';
import {FontFamily} from '../../ui/styles';

import {assetKeyToString} from './Utils';

export const ForeignNode: React.FC<{assetKey: {path: string[]}}> = ({assetKey}) => (
  <ForeignNodeLink>
    <span className="label">{assetKeyToString(assetKey)}</span>
    <IconWIP name="open_in_new" color={ColorsWIP.Gray500} />
  </ForeignNodeLink>
);

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
  return {width: assetKeyToString({path}).length * 7 + 30, height: 30};
};
