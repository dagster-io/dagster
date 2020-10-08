import {Collapse, Colors, Icon} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

interface ISidebarSectionProps {
  title: string;
  collapsedByDefault?: boolean;
}

interface ISidebarSectionState {
  isOpen: boolean;
}

export class SidebarSection extends React.Component<ISidebarSectionProps, ISidebarSectionState> {
  storageKey: string;

  constructor(props: ISidebarSectionProps) {
    super(props);

    this.storageKey = `sidebar-${props.title}`;
    this.state = {
      isOpen: {
        true: true,
        false: false,
        null: this.props.collapsedByDefault === true ? false : true,
      }[`${window.localStorage.getItem(this.storageKey)}`],
    };
  }

  onToggle = () => {
    const isOpen = !this.state.isOpen;
    this.setState({isOpen});
    window.localStorage.setItem(this.storageKey, `${isOpen}`);
  };

  render() {
    const {isOpen} = this.state;

    return (
      <div>
        <CollapsingHeaderBar onClick={this.onToggle}>
          {this.props.title}
          <DisclosureIcon icon={isOpen ? IconNames.CHEVRON_DOWN : IconNames.CHEVRON_UP} />
        </CollapsingHeaderBar>
        <Collapse isOpen={isOpen}>
          <SectionInner>{this.props.children}</SectionInner>
        </Collapse>
      </div>
    );
  }
}

export const DisclosureIcon = styled(Icon)`
  float: right;
  opacity: 0.5;
`;

export const SidebarTitle = styled.h3`
  font-family: 'Source Code Pro', monospace;
  margin: 0;
  margin-bottom: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
`;

export const SectionHeader = styled.h4`
  font-family: 'Source Code Pro', monospace;
  font-size: 15px;
  margin: 6px 0;
`;

export const SectionSmallHeader = styled.h4`
  font-family: 'Source Code Pro', monospace;
  font-size: 14px;
  font-weight: 500;
  margin: 6px 0;
`;

export const SidebarDivider = styled.div`
  height: 2px;
  background: ${Colors.GRAY4};
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

export const SectionInner = styled.div`
  padding: 12px;
`;
