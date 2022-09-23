import {Colors, Icon, FontFamily} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';
import { ReconcileBadge } from './AssetNode';

import {displayNameForAssetKey} from './Utils';

export const ForeignNode: React.FC<{
  assetKey: {path: string[]};
  backgroundColor?: string;
  reconcile?: boolean;
}> = React.memo(({assetKey, backgroundColor, reconcile}) => (
  <ForeignNodeLink style={{backgroundColor}}>
    <span className="label">{displayNameForAssetKey(assetKey)}</span>
    {reconcile ? <ReconcileBadge>R</ReconcileBadge> : null}
    <ReconcileBadge>R</ReconcileBadge>
    <Icon name="open_in_new" color={Colors.Gray500} />
  </ForeignNodeLink>
));

const ForeignNodeLink = styled.div`
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
