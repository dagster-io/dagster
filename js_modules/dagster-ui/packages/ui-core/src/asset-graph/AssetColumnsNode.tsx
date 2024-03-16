import {Box, Caption, Tooltip} from '@dagster-io/ui-components';

import {
  AssetInsetForHoverEffect,
  AssetNameRow,
  AssetNodeBox,
  AssetNodeContainer,
} from './AssetNode';
import {AssetNodeFragment} from './types/AssetNode.types';
import {AssetColumnLineageLocal} from '../assets/lineage/useColumnLineageDataForAssets';
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
        <AssetNodeBox $selected={selected} $isSource={definition.isSource}>
          <AssetNameRow definition={definition} />
          <Box style={{height: height - 60}} flex={{direction: 'column'}}></Box>
        </AssetNodeBox>
      </AssetNodeContainer>
    </AssetInsetForHoverEffect>
  );
};

export const AssetColumnNode = ({column}: {column: AssetColumnLineageLocal['']}) => {
  return (
    <Box style={{width: '100%', height: 32}} flex={{direction: 'column'}}>
      <Tooltip key={column.name} content={column.description || 'No description provided'}>
        <Box
          style={{height: 32}}
          padding={{left: 8, right: 4}}
          flex={{gap: 4, justifyContent: 'space-between', alignItems: 'center'}}
        >
          <Caption>{column.name}</Caption>
          <TypeTag type={column.type || ''} />
        </Box>
      </Tooltip>
    </Box>
  );
};
