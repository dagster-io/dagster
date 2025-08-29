import {Box, Colors, HoverButton, Icon, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';

import {AssetSidebarListView, AssetSidebarListViewProps} from './AssetSidebarListView';

interface TreeViewPanelProps extends AssetSidebarListViewProps {
  title: string;
  tooltipContent: string;
  expandedPanel: 'bottom' | 'top' | null;
  setExpandedPanel: React.Dispatch<React.SetStateAction<'bottom' | 'top' | null>>;
  position: 'top' | 'bottom';
  isHidden: boolean;
}

export const TreeViewPanel = ({
  title,
  tooltipContent,
  expandedPanel,
  setExpandedPanel,
  position,
  isHidden,
  ...listViewProps
}: TreeViewPanelProps) => {
  const isExpanded = expandedPanel === position;

  return (
    <Box flex={{direction: 'column', gap: 4}}>
      <Box
        background={Colors.backgroundLight()}
        padding={{horizontal: 24, vertical: 8}}
        style={{fontWeight: 500, position: 'sticky', top: 0, zIndex: 1}}
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        border={isHidden ? 'top' : 'top-and-bottom'}
      >
        <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
          {title}{' '}
          <Tooltip content={tooltipContent}>
            <Icon name="info" />
          </Tooltip>
        </Box>
        <Box>
          <HoverButton
            onClick={() => {
              setExpandedPanel((prev) => (prev !== position ? position : null));
            }}
          >
            <Icon name={isExpanded ? 'collapse_arrows' : 'expand_arrows'} />
          </HoverButton>
        </Box>
      </Box>
      <div
        style={{
          display: isHidden ? 'none' : 'block',
          height: '100%',
          overflow: 'hidden',
        }}
      >
        <AssetSidebarListView {...listViewProps} />
      </div>
    </Box>
  );
};
