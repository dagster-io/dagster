import {Box, Caption, Tooltip} from '@dagster-io/ui-components';

import {
  AssetInsetForHoverEffect,
  AssetNameRow,
  AssetNodeBox,
  AssetNodeContainer,
} from './AssetNode';
import {AssetNodeFragment} from './types/AssetNode.types';
import {AssetColumnLineageLocal} from '../assets/lineage/useColumnLineageDataForAssets';
import {AssetComputeKindTag} from '../graph/OpTags';
import {TypeTag} from '../metadata/TableSchema';

export const AssetColumnsNode = ({
  selected,
  definition,
  columns,
}: {
  selected: boolean;
  definition: AssetNodeFragment;
  columns: AssetColumnLineageLocal[''][];
}) => {
  return (
    <AssetInsetForHoverEffect style={{opacity: columns.length > 0 ? 1 : 0.4}}>
      <AssetNodeContainer $selected={selected}>
        <div style={{minHeight: 24}} />
        <AssetNodeBox $selected={selected} $isSource={definition.isSource}>
          <AssetNameRow definition={definition} />
          <Box style={{padding: '6px 8px'}} flex={{direction: 'column'}}>
            {columns.map((c) => (
              <Tooltip key={c.name} content={c.description || 'No description provided'}>
                <Box flex={{gap: 4, justifyContent: 'space-between', alignItems: 'center'}}>
                  <Caption>{c.name}</Caption>
                  <TypeTag type={c.type || ''} />
                </Box>
              </Tooltip>
            ))}
          </Box>
        </AssetNodeBox>
        <AssetComputeKindTag definition={definition} style={{right: -2, paddingTop: 7}} />
      </AssetNodeContainer>
    </AssetInsetForHoverEffect>
  );
};
