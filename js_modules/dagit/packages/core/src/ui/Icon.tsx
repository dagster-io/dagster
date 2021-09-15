import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';

// Based directly on Material Icons font names.
type IconName =
  | 'account_tree'
  | 'alternate_email'
  | 'arrow_left'
  | 'arrow_drop_down'
  | 'assignment'
  | 'assignment_turned_in'
  | 'cached'
  | 'close'
  | 'done'
  | 'error'
  | 'expand_more'
  | 'filter_alt'
  | 'folder'
  | 'folder_open'
  | 'info'
  | 'history'
  | 'open_in_new'
  | 'search'
  | 'sensors'
  | 'settings'
  | 'source'
  | 'star'
  | 'toggle_off'
  | 'toggle_on'
  | 'visibility'
  | 'warning'
  | 'workspaces';

interface Props {
  color?: string;
  name: IconName;
  size?: 16 | 24;
}

export const IconWIP = (props: Props) => {
  const {color = ColorsWIP.Dark, name, size = 16} = props;
  return (
    <IconWrapper $size={size} $color={color} className="material-icons">
      {name}
    </IconWrapper>
  );
};

export const IconWrapper = styled.span<{$color: string; $size: number}>`
  color: ${({$color}) => `${$color}`};
  font-size: ${({$size}) => `${$size}px`};
`;
