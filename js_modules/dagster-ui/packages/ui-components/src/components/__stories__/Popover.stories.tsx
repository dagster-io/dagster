import {Box} from '../Box';
import {Button} from '../Button';
import {Icon} from '../Icon';
import {Menu, MenuItem} from '../Menu';
import {GlobalPopoverStyle, Popover} from '../Popover';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Popover',
  component: Popover,
};

export const Default = () => {
  return (
    <>
      <GlobalPopoverStyle />
      <Box flex={{direction: 'column', gap: 8, alignItems: 'flex-start'}} padding={8}>
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
          <Button intent="primary" rightIcon={<Icon name="expand_more" />}>
            Do important things
          </Button>
        </Popover>
      </Box>
    </>
  );
};
