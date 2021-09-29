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
    <div>
      <CollapsingHeaderBar onClick={onToggle}>
        {title}
        <DisclosureIcon name={open ? 'expand_more' : 'chevron_left'} />
      </CollapsingHeaderBar>
      <Collapse isOpen={open}>
        <div>{children}</div>
      </Collapse>
    </div>
  );
};

const DisclosureIcon = styled(IconWIP)`
  opacity: 0.5;
`;

export const SidebarTitle = styled.h3`
  font-family: ${FontFamily.monospace};
  font-size: 16px;
  margin: 0;
  margin-bottom: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
`;

export const SectionHeader = styled.h4`
  font-family: ${FontFamily.monospace};
  font-size: 18px;
  margin: 2px 0 0 0;
`;

export const SectionSmallHeader = styled.h4`
  font-family: ${FontFamily.monospace};
  font-size: 16px;
  font-weight: 500;
  margin: 2px 0;
`;

export const SidebarSubhead = styled.div`
  color: ${ColorsWIP.Gray400};
  font-size: 0.7rem;
`;

export const SectionItemContainer = styled.div`
  border-bottom: 1px solid ${ColorsWIP.Gray100};
  margin-bottom: 20px;
  padding-bottom: 20px;
  font-size: 0.8rem;
  &:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 5px;
  }
`;

// Internal

const CollapsingHeaderBar = styled.div`
  padding: 6px;
  padding-left: 12px;
  background: linear-gradient(to bottom, ${ColorsWIP.Gray50}, ${ColorsWIP.Gray100});
  border-top: 1px solid ${ColorsWIP.Gray100};
  border-bottom: 1px solid ${ColorsWIP.Gray100};
  color: ${ColorsWIP.Gray600};
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  text-transform: uppercase;
  font-size: 0.75rem;
`;
