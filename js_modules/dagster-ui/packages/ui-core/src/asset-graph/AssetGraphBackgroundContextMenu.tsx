import * as React from 'react';

import {ContextMenuWrapper} from './ContextMenuWrapper';
import {AssetGraphSettingsMenu} from './GraphSettings';

type Props = {
  direction: 'vertical' | 'horizontal';
  setDirection: (dir: 'vertical' | 'horizontal') => void;
  children: React.ReactNode;

  allGroups?: string[];
  expandedGroups?: string[];
  setExpandedGroups?: (groups: string[]) => void;
  hideEdgesToNodesOutsideQuery?: boolean;
  setHideEdgesToNodesOutsideQuery?: (hideEdgesToNodesOutsideQuery: boolean) => void;
};

export const AssetGraphBackgroundContextMenu = (props: Props) => {
  const {children, ...menuProps} = props;
  return (
    <ContextMenuWrapper
      wrapperOuterStyles={{width: '100%', height: '100%'}}
      wrapperInnerStyles={{width: '100%', height: '100%'}}
      menu={<AssetGraphSettingsMenu {...menuProps} />}
    >
      {children}
    </ContextMenuWrapper>
  );
};
