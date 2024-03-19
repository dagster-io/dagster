import {Box, Caption, Colors, Icon, StyledTag, Tooltip} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {
  AssetInsetForHoverEffect,
  AssetNameRow,
  AssetNodeBox,
  AssetNodeContainer,
} from './AssetNode';
import {AssetNodeFragment} from './types/AssetNode.types';
import {Timestamp} from '../app/time/Timestamp';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetColumnLineageLocalColumn} from '../assets/lineage/useColumnLineageDataForAssets';
import {AssetComputeKindTag} from '../graph/OpTags';
import {AssetKeyInput} from '../graphql/types';
import {iconForColumnType} from '../metadata/TableSchema';
import {Description} from '../pipelines/Description';

export const AssetColumnsGroupNode = ({
  selected,
  definition,
  height,
  asOf,
}: {
  selected: boolean;
  definition: AssetNodeFragment;
  asOf: string | undefined;
  height: number;
}) => {
  return (
    <AssetInsetForHoverEffect style={{marginLeft: 12, marginRight: 12}}>
      <AssetNodeContainer $selected={selected}>
        <div style={{minHeight: 24}} />
        <AssetNodeBox $selected={selected} $isSource={definition.isSource} $noScale>
          <AssetNameRow definition={definition} />
          <Box style={{height: height - 60}} flex={{direction: 'column'}}></Box>
          <Box border="top" padding={{horizontal: 8, vertical: 2}} style={{minHeight: 22}}>
            {asOf ? (
              <Caption color={Colors.textLighter()}>
                <Timestamp timestamp={{ms: Number(asOf)}} />
              </Caption>
            ) : undefined}
          </Box>
        </AssetNodeBox>
        <AssetComputeKindTag definition={definition} style={{right: 10, paddingTop: 7}} />
      </AssetNodeContainer>
    </AssetInsetForHoverEffect>
  );
};

export const AssetColumnNode = ({
  assetKey,
  column,
  blueBackground,
}: {
  assetKey: AssetKeyInput;
  column: AssetColumnLineageLocalColumn;
  blueBackground: boolean;
}) => {
  const icon = iconForColumnType(column.type ?? '');

  return (
    <Box flex={{direction: 'column'}}>
      <Tooltip
        key={column.name}
        position="bottom-left"
        content={
          <div style={{maxWidth: 500}}>
            <Description
              maxHeight={400}
              description={column.description || 'No description provided'}
            />
          </div>
        }
      >
        <ColumnLink
          to={assetDetailsPathForKey(assetKey, {view: 'lineage', column: column.name})}
          $blueBackground={blueBackground}
        >
          {icon ? <Icon name={icon} /> : <span style={{width: 16}} />}
          <Caption style={{whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>
            {column.name}
          </Caption>
        </ColumnLink>
      </Tooltip>
    </Box>
  );
};

const ColumnLink = styled(Link)<{$blueBackground: boolean}>`
  height: 28px;
  margin: 2px 12px;
  padding-left: 2px;
  padding-right: 4px;
  display: flex;
  gap: 4px;
  align-items: center;
  transition: background 100ms linear;
  border-radius: 8px;

  ${StyledTag} {
    background: none;
    color: ${Colors.textLight()};
  }
  ${(p) =>
    p.$blueBackground
      ? `
    background: ${Colors.backgroundBlue()}`
      : `
    &:hover {
      text-decoration: none;
      background: ${Colors.backgroundLightHover()};
    }`}
`;
