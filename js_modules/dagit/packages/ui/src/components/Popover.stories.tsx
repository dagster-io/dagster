import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {ButtonWIP} from './Button';
import {Group} from './Group';
import {IconWIP} from './Icon';
import {MenuWIP as Menu, MenuItemWIP as MenuItem} from './Menu';
import {GlobalPopoverStyle, Popover} from './Popover';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Popover',
  component: Popover,
} as Meta;

export const Default = () => {
  return (
    <>
      <GlobalPopoverStyle />
      <Group direction="column" spacing={8} padding={8}>
        <Popover
          position="bottom-left"
          content={
            <Menu>
              <MenuItem icon="layers" text="Act fast" />
              <MenuItem icon="history" text="Act slow" />
              <MenuItem icon="delete" intent="danger" text="Delete it all" />
            </Menu>
          }
        >
          <ButtonWIP intent="primary" rightIcon={<IconWIP name="expand_more" />}>
            Do important things
          </ButtonWIP>
        </Popover>
      </Group>
    </>
  );
};
