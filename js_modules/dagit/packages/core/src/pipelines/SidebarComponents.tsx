import {Collapse, Colors, Icon} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

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
        <DisclosureIcon icon={open ? IconNames.CHEVRON_DOWN : IconNames.CHEVRON_UP} />
      </CollapsingHeaderBar>
      <Collapse isOpen={open}>
        <div>{children}</div>
      </Collapse>
    </div>
  );
};

const DisclosureIcon = styled(Icon)`
  float: right;
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
  color: ${Colors.GRAY3};
  font-size: 0.7rem;
`;

export const SectionItemContainer = styled.div`
  border-bottom: 1px solid ${Colors.LIGHT_GRAY2};
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
  background: linear-gradient(to bottom, ${Colors.LIGHT_GRAY5}, ${Colors.LIGHT_GRAY4});
  border-top: 1px solid ${Colors.LIGHT_GRAY4};
  border-bottom: 1px solid ${Colors.LIGHT_GRAY3};
  color: ${Colors.GRAY1};
  text-transform: uppercase;
  font-size: 0.75rem;
`;
