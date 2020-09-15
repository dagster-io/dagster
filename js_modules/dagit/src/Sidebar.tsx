import * as React from 'react';
import styled from 'styled-components/macro';
import {Colors} from '@blueprintjs/core';

interface ISidebarProps {
  onClose: () => void;
}

export default class Sidebar extends React.Component<ISidebarProps, {}> {
  render() {
    return (
      <SidebarWrapper>
        <SidebarCloseButton role="button" onClick={this.props.onClose}>
          {'<'} Close
        </SidebarCloseButton>
        <SidebarContent>{this.props.children}</SidebarContent>
      </SidebarWrapper>
    );
  }
}

const SidebarWrapper = styled.div`
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 30%;
  max-width: 600px;
  background-color: white;
  z-index: 2;
  border-left: 1px solid ${Colors.GRAY5};
`;

const SidebarContent = styled.div`
  padding: 5px;
`;

const SidebarCloseButton = styled.div`
  height: 51px;
  border: none none solid none;
  border-bottom: 1px solid ${Colors.GRAY5};
  background-color: white;
  border-radius: 0;
  width: 100%;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
`;
