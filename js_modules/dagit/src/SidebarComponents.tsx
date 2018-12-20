import * as React from "react";
import styled from "styled-components";
import { Icon, Colors, Collapse } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";

interface ISidebarSectionProps {
  title: string;
  collapsedByDefault?: boolean;
}

interface ISidebarSectionState {
  isOpen: boolean;
}

export class SidebarSection extends React.Component<
  ISidebarSectionProps,
  ISidebarSectionState
> {
  state = {
    isOpen: this.props.collapsedByDefault === true ? false : true
  };

  render() {
    const { isOpen } = this.state;

    return (
      <div>
        <SectionHeader onClick={() => this.setState({ isOpen: !isOpen })}>
          {this.props.title}
          <DisclosureIcon
            icon={isOpen ? IconNames.CHEVRON_DOWN : IconNames.CHEVRON_UP}
          />
        </SectionHeader>
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
  font-family: "Source Code Pro", monospace;
  margin: 0;
  margin-bottom: 14px;
  overflow: hidden;
  padding-left: 12px;
  text-overflow: ellipsis;
`;

export const SectionItemHeader = styled.h4`
  font-family: "Source Code Pro", monospace;
  font-size: 15px;
  margin: 6px 0;
`;

export const SidebarSubhead = styled.div`
  color: ${Colors.GRAY3};
  font-size: 0.7rem;
  margin-left: 12px;
  margin-top: 14px;
`;
export const SectionItemContainer = styled.div`
  border-bottom: 1px solid ${Colors.LIGHT_GRAY2};
  margin-bottom: 20px;
  padding-bottom: 20px;
  &:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 5px;
  }
`;

// Internal

const SectionHeader = styled.div`
  padding: 6px;
  padding-left: 12px;
  background: linear-gradient(
    to bottom,
    ${Colors.LIGHT_GRAY5},
    ${Colors.LIGHT_GRAY4}
  );
  border-top: 1px solid ${Colors.LIGHT_GRAY4};
  border-bottom: 1px solid ${Colors.LIGHT_GRAY3};
  color: ${Colors.GRAY1};
  text-transform: uppercase;
  font-size: 0.75rem;
`;

const SectionInner = styled.div`
  padding: 12px;
`;
