import * as React from "react";
import styled from "styled-components";
import { Colors, Collapse } from "@blueprintjs/core";

interface ISidebarSectionProps {
  title: string;
}

interface ISidebarSectionState {
  isOpen: boolean;
}

export class SidebarSection extends React.Component<
  ISidebarSectionProps,
  ISidebarSectionState
> {
  state = {
    isOpen: true
  };

  render() {
    return (
      <div>
        <SectionHeader
          onClick={() => this.setState({ isOpen: !this.state.isOpen })}
        >
          {this.props.title}
        </SectionHeader>
        <Collapse isOpen={this.state.isOpen}>
          <SectionInner>{this.props.children}</SectionInner>
        </Collapse>
      </div>
    );
  }
}

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
  margin: 8px 0;
`;

export const SidebarSubhead = styled.div`
  color: ${Colors.GRAY3};
  font-size: 0.7rem;
  margin-left: 12px;
  margin-top: 14px;
`;
export const SectionItemContainer = styled.div`
  margin-bottom: 10px;
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
