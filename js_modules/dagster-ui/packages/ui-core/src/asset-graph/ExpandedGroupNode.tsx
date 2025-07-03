import {Box, Icon} from '@dagster-io/ui-components';
import clsx from 'clsx';
import * as React from 'react';

import {GroupNodeNameAndRepo, useGroupNodeContextMenu} from './CollapsedGroupNode';
import {ContextMenuWrapper} from './ContextMenuWrapper';
import {GraphNode} from './Utils';
import styles from './css/ExpandedGroupNode.module.css';
import {GroupLayout} from './layout';
import {SVGRelativeContainerForSafari} from '../graph/SVGComponents';

export const ExpandedGroupNode = ({
  group,
  minimal,
  onCollapse,
  toggleSelectAllNodes,
  preferredJobName,
  onFilterToGroup,
  setHighlighted,
}: {
  group: GroupLayout & {assets: GraphNode[]};
  minimal: boolean;
  onCollapse?: () => void;
  toggleSelectAllNodes?: (e: React.MouseEvent) => void;
  preferredJobName?: string;
  onFilterToGroup?: () => void;
  setHighlighted: (ids: string[] | null) => void;
}) => {
  const {menu, dialog} = useGroupNodeContextMenu({
    onFilterToGroup,
    assets: group.assets,
    preferredJobName,
  });
  return (
    <SVGRelativeContainerForSafari>
      <ContextMenuWrapper menu={menu} stopPropagation>
        <div
          className={clsx(styles.groupNodeHeaderBox, minimal ? styles.minimal : null)}
          onMouseEnter={() => setHighlighted(group.assets.map((a) => a.id))}
          onMouseLeave={() => setHighlighted(null)}
          onClick={(e) => {
            if (e.metaKey && toggleSelectAllNodes) {
              toggleSelectAllNodes(e);
            } else {
              onCollapse?.();
            }
            e.stopPropagation();
          }}
        >
          <GroupNodeNameAndRepo group={group} minimal={minimal} />
          {onCollapse && (
            <Box padding={{vertical: 4}}>
              <Icon name="unfold_less" />
            </Box>
          )}
        </div>
      </ContextMenuWrapper>
      {dialog}
    </SVGRelativeContainerForSafari>
  );
};

export const GroupOutline = ({minimal}: {minimal: boolean}) => (
  <SVGRelativeContainerForSafari>
    <div className={clsx(styles.groupOutlineBox, minimal ? styles.minimal : null)} />
  </SVGRelativeContainerForSafari>
);
