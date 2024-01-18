import {Box, Colors, FontFamily, Icon, Menu, MenuItem} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {AssetDescription, NameTooltipCSS} from './AssetNode';
import {ContextMenuWrapper} from './ContextMenuWrapper';
import {GraphNode} from './Utils';
import {GroupLayout} from './layout';
import {withMiddleTruncation} from '../app/Util';
import {CalculateChangedAndMissingDialog} from '../assets/CalculateChangedAndMissingDialog';
import {useMaterializationAction} from '../assets/LaunchAssetExecutionButton';
import {AssetKey} from '../assets/types';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';

export const GroupNodeNameAndRepo = ({group, minimal}: {minimal: boolean; group: GroupLayout}) => {
  const name = `${group.groupName} `;
  const location = repoAddressAsHumanString({
    name: group.repositoryName,
    location: group.repositoryLocationName,
  });

  if (minimal) {
    return (
      <Box style={{flex: 1, fontFamily: FontFamily.monospace}}>
        <div
          data-tooltip={name}
          data-tooltip-style={GroupNameTooltipStyle}
          style={{fontSize: 30, fontWeight: 600, lineHeight: '30px'}}
        >
          {withMiddleTruncation(name, {maxLength: 14})}
        </div>
      </Box>
    );
  }
  return (
    <Box style={{flex: 1, fontFamily: FontFamily.monospace}}>
      <Box flex={{direction: 'row', gap: 4}}>
        <div
          data-tooltip={name}
          data-tooltip-style={GroupNameTooltipStyle}
          style={{fontSize: 20, fontWeight: 600, lineHeight: '1.1em'}}
        >
          {withMiddleTruncation(name, {maxLength: 22})}
        </div>
      </Box>
      <Box style={{lineHeight: '1em', color: Colors.textLight()}}>
        {withMiddleTruncation(location, {maxLength: 31})}
      </Box>
    </Box>
  );
};

export const CollapsedGroupNode = ({
  group,
  minimal,
  onExpand,
  toggleSelectAllNodes,
  preferredJobName,
  onFilterToGroup,
}: {
  minimal: boolean;
  onExpand: () => void;
  toggleSelectAllNodes?: (e: React.MouseEvent) => void;
  group: GroupLayout & {assetCount: number; assets: GraphNode[]};
  preferredJobName: string;
  onFilterToGroup: () => void;
}) => {
  const {menu, dialog} = useGroupNodeContextMenu({
    onFilterToGroup,
    assets: group.assets,
    preferredJobName,
  });
  return (
    <ContextMenuWrapper menu={menu} stopPropagation>
      <CollapsedGroupNodeContainer
        onClick={(e) => {
          if (e.metaKey && toggleSelectAllNodes) {
            toggleSelectAllNodes(e);
          } else {
            onExpand();
          }
          e.stopPropagation();
        }}
      >
        <CollapsedGroupNodeBox $minimal={minimal}>
          <Box padding={{vertical: 8, left: 12, right: 8}} flex={{}}>
            <GroupNodeNameAndRepo group={group} minimal={minimal} />
            <Box padding={{vertical: 4}}>
              <Icon name="unfold_more" />
            </Box>
          </Box>
          {!minimal && (
            <Box padding={{horizontal: 12, bottom: 4}}>
              <AssetDescription $color={Colors.textLighter()}>
                {group.assetCount} {group.assetCount === 1 ? 'asset' : 'assets'}
              </AssetDescription>
            </Box>
          )}
        </CollapsedGroupNodeBox>
        <GroupStackLine style={{width: '94%', marginLeft: '3%'}} />
        <GroupStackLine style={{width: '88%', marginLeft: '6%'}} />
      </CollapsedGroupNodeContainer>
      {dialog}
    </ContextMenuWrapper>
  );
};

export const useGroupNodeContextMenu = ({
  onFilterToGroup,
  assets,
  preferredJobName,
}: {
  onFilterToGroup?: () => void;
  assets: GraphNode[];
  preferredJobName?: string;
}) => {
  const {onClick, launchpadElement} = useMaterializationAction(preferredJobName);
  const [showCalculatingChangedAndMissingDialog, setShowCalculatingChangedAndMissingDialog] =
    React.useState<boolean>(false);

  const menu = (
    <Menu>
      <MenuItem
        icon="materialization"
        text={`Materialize assets (${assets.length})`}
        onClick={(e) => {
          onClick(
            assets.map((asset) => asset.assetKey),
            e,
          );
        }}
      />
      <MenuItem
        icon="changes_present"
        text="Materialize changed and missing"
        onClick={() => setShowCalculatingChangedAndMissingDialog(true)}
      />
      {onFilterToGroup ? (
        <MenuItem text="Filter to this group" onClick={onFilterToGroup} icon="filter_alt" />
      ) : null}
    </Menu>
  );
  const dialog = (
    <div>
      <CalculateChangedAndMissingDialog
        isOpen={!!showCalculatingChangedAndMissingDialog}
        onClose={() => {
          setShowCalculatingChangedAndMissingDialog(false);
        }}
        assets={assets}
        onMaterializeAssets={(assets: AssetKey[], e: React.MouseEvent<any>) => {
          onClick(assets, e);
        }}
      />
      {launchpadElement}
    </div>
  );

  return {menu, dialog};
};

export const GroupNameTooltipStyle = JSON.stringify({
  ...NameTooltipCSS,
  background: Colors.backgroundLight(),
  border: `none`,
  borderRadius: '4px',
});

const GroupStackLine = styled.div`
  background: transparent;
  border-top: 2px solid ${Colors.lineageGroupNodeBorder()};
  border-radius: 2px;
`;

const CollapsedGroupNodeBox = styled.div<{$minimal: boolean}>`
  border: ${(p) => (p.$minimal ? '4px' : '2px')} solid ${Colors.lineageGroupNodeBorder()};
  background: ${Colors.backgroundLight()};
  border-radius: 8px;
  position: relative;
  margin-top: 8px;
`;

const CollapsedGroupNodeContainer = styled.div`
  user-select: none;
  padding: 4px;
  transition:
    transform linear 200ms,
    gap linear 200ms;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;

  &:hover {
    transform: scale(1.03);
    gap: 3px;
    ${CollapsedGroupNodeBox} {
      transition: background linear 200ms;
      background: ${Colors.backgroundLightHover()};
    }
  }
`;
