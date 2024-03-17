import {Box, Caption, Colors, StyledTag, Tooltip} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {
  AssetInsetForHoverEffect,
  AssetNameRow,
  AssetNodeBox,
  AssetNodeContainer,
} from './AssetNode';
import {AssetNodeFragment} from './types/AssetNode.types';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetColumnLineageLocal} from '../assets/lineage/useColumnLineageDataForAssets';
import {AssetKeyInput} from '../graphql/types';
import {TypeTag} from '../metadata/TableSchema';

export const AssetColumnsGroupNode = ({
  selected,
  definition,
  height,
}: {
  selected: boolean;
  definition: AssetNodeFragment;
  height: number;
}) => {
  return (
    <AssetInsetForHoverEffect>
      <AssetNodeContainer $selected={selected}>
        <div style={{minHeight: 24}} />
        <AssetNodeBox $selected={selected} $isSource={definition.isSource} $noScale>
          <AssetNameRow definition={definition} />
          <Box style={{height: height - 60}} flex={{direction: 'column'}}></Box>
        </AssetNodeBox>
      </AssetNodeContainer>
    </AssetInsetForHoverEffect>
  );
};

export const AssetColumnNode = ({
  assetKey,
  column,
  selected,
}: {
  assetKey: AssetKeyInput;
  column: AssetColumnLineageLocal[''];
  selected: boolean;
}) => {
  return (
    <Box style={{width: '100%', height: 32}} flex={{direction: 'column'}}>
      <Tooltip key={column.name} content={column.description || 'No description provided'}>
        <ColumnLink
          to={assetDetailsPathForKey(assetKey, {view: 'lineage', column: column.name})}
          $selected={selected}
        >
          <Caption>{column.name}</Caption>
          <TypeTag type={column.type || ''} />
        </ColumnLink>
      </Tooltip>
    </Box>
  );
};

const ColumnLink = styled(Link)<{$selected: boolean}>`
  height: 28px;
  margin: 2px 0;
  padding-left: 8px;
  padding-right: 4px;
  display: flex;
  gap: 4px;
  justify-content: space-between;
  align-items: center;
  transition: background 100ms linear;
  border-radius: 8px;

  ${StyledTag} {
    background: none;
    color: ${Colors.textLight()};
  }
  ${(p) =>
    p.$selected
      ? `
    background: ${Colors.backgroundBlue()}`
      : `
    &:hover {
      text-decoration: none;
      background: ${Colors.backgroundLightHover()};
    }`}
`;
