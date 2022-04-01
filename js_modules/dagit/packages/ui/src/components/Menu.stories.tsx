import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Group} from './Group';
import {Menu, MenuItem, MenuDivider} from './Menu';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Menu',
  component: Menu,
} as Meta;

export const Default = () => {
  return (
    <Group direction="column" spacing={8} padding={8}>
      <Container style={{width: '180px'}}>
        <Menu>
          <MenuItem text="Item 01" />
          <MenuItem text="Item 02" />
          <MenuItem text="Item 03" />
        </Menu>
      </Container>
      <Container style={{width: '180px'}}>
        <Menu>
          <MenuItem icon="folder" text="Item 01" />
          <MenuItem icon="location_on" text="Item 02" />
          <MenuItem icon="download_for_offline" text="Item 03" />
          <MenuDivider />
          <MenuItem icon="attach_file" text="Item 04" />
        </Menu>
      </Container>
      <Container style={{width: '180px'}}>
        <Menu>
          <MenuItem icon="download_for_offline" text="Save" />
          <MenuItem icon="attach_file" text="Attach" />
          <MenuItem intent="danger" icon="delete" text="Delete" />
        </Menu>
      </Container>
    </Group>
  );
};

const Container = styled.div`
  box-shadow: rgba(0, 0, 0, 0.12) 0px 2px 12px;
`;
