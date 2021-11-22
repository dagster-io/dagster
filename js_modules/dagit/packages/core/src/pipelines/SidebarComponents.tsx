import {Collapse} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
import {FontFamily} from '../ui/styles';

interface ISidebarSectionProps {
  title: string;
  collapsedByDefault?: boolean;
}

export const SidebarSection: React.FC<ISidebarSectionProps> = (props) => {
  const {title, collapsedByDefault, children} = props;
  const storageKey = `sidebar-${title}`;

  const [open, setOpen] = React.useState(() => {
    const stored = window.localStorage.getItem(storageKey);
    if (stored === 'true' || stored === 'false') {
      return stored === 'true';
    }
    return !collapsedByDefault;
  });

  const onToggle = React.useCallback(() => {
    setOpen((current) => {
      window.localStorage.setItem(storageKey, `${!current}`);
      return !current;
    });
  }, [storageKey]);

  return (
    <>
      <CollapsingHeaderBar onClick={onToggle}>
        {title}
        <IconWIP
          size={24}
          name="arrow_drop_down"
          style={{transform: open ? 'rotate(0)' : 'rotate(-90deg)'}}
        />
      </CollapsingHeaderBar>
      <Collapse isOpen={open}>
        <div>{children}</div>
      </Collapse>
    </>
  );
};

export const SidebarTitle = styled.h3`
  font-family: ${FontFamily.monospace};
  font-size: 16px;
  margin: 0 0 12px;
  overflow: hidden;
  text-overflow: ellipsis;

  :first-child:last-child {
    margin-bottom: 0;
  }
`;

export const SectionHeader = styled.h4`
  font-family: ${FontFamily.monospace};
  font-size: 16px;
  margin: 2px 0 0 0;
`;

export const SectionSmallHeader = styled.h4`
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  font-weight: 500;
  margin: 2px 0;
`;

export const SidebarSubhead = styled.div`
  color: ${ColorsWIP.Gray400};
  font-size: 0.7rem;
`;

export const SectionItemContainer = styled.div`
  border-bottom: 1px solid ${ColorsWIP.KeylineGray};
  margin-bottom: 12px;
  padding-bottom: 12px;
  font-size: 0.8rem;
  &:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
  }
`;

const CollapsingHeaderBar = styled.div`
  height: 32px;
  padding-left: 24px;
  padding-right: 8px;
  background: ${ColorsWIP.White};
  border-top: 1px solid ${ColorsWIP.KeylineGray};
  border-bottom: 1px solid ${ColorsWIP.KeylineGray};
  color: ${ColorsWIP.Gray900};
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  font-weight: 700;
  user-select: none;
`;
