import {Meta} from '@storybook/react';

import {Box} from '../Box';
import {Button, JoinedButtons} from '../Button';
import {Colors} from '../Color';
import {Group} from '../Group';
import {Icon} from '../Icon';
import {Menu, MenuItem} from '../Menu';
import {Popover} from '../Popover';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Button',
  component: Button,
} as Meta;

export const Default = () => {
  return (
    <Group direction="column" spacing={8}>
      <Button>Button</Button>
      <Button icon={<Icon name="star" />}>Button</Button>
      <Button rightIcon={<Icon name="close" />}>Button</Button>
      <Button icon={<Icon name="source" />} rightIcon={<Icon name="expand_more" />}>
        Button
      </Button>
      <Button icon={<Icon name="cached" />} />
      <Box
        background={Colors.backgroundLight()}
        padding={16}
        flex={{direction: 'column', alignItems: 'stretch'}}
        style={{width: 320}}
      >
        <Button>Full-width Flex Child</Button>
      </Box>
    </Group>
  );
};

export const Intent = () => {
  return (
    <Group direction="column" spacing={8}>
      <Button icon={<Icon name="star" />}>Intent not defined</Button>
      <Button icon={<Icon name="star" />} intent="primary">
        Primary
      </Button>
      <Button icon={<Icon name="done" />} intent="success">
        Success
      </Button>
      <Button icon={<Icon name="error" />} intent="danger">
        Danger
      </Button>
      <Button icon={<Icon name="warning" />} intent="warning">
        Warning
      </Button>
      <Button icon={<Icon name="star" />} intent="none">
        None
      </Button>
    </Group>
  );
};

export const Outlined = () => {
  return (
    <Group direction="column" spacing={8}>
      <Button outlined icon={<Icon name="star" />}>
        Intent not defined
      </Button>
      <Button outlined icon={<Icon name="star" />} intent="primary">
        Primary
      </Button>
      <Button outlined icon={<Icon name="done" />} intent="success">
        Success
      </Button>
      <Button outlined icon={<Icon name="error" />} intent="danger">
        Danger
      </Button>
      <Button outlined icon={<Icon name="warning" />} intent="warning">
        Warning
      </Button>
      <Button outlined icon={<Icon name="star" />} intent="none">
        None
      </Button>
    </Group>
  );
};

export const Disabled = () => {
  return (
    <Group direction="column" spacing={8}>
      <Button icon={<Icon name="star" />} intent="primary">
        Enabled
      </Button>
      <Button icon={<Icon name="cached" />} disabled intent="primary">
        Disabled
      </Button>
      <Button icon={<Icon name="cached" />} loading intent="primary">
        Loading
      </Button>
      <Button loading intent="primary">
        Loading with no icon
      </Button>
      <Button rightIcon={<Icon name="cached" />} loading intent="primary">
        Loading right
      </Button>
      <Button
        icon={<Icon name="cached" />}
        rightIcon={<Icon name="folder" />}
        loading
        intent="primary"
      >
        Loading with two icons
      </Button>
      <Button outlined icon={<Icon name="cached" />} disabled intent="primary">
        Disabled outlined
      </Button>
      <Button outlined loading icon={<Icon name="cached" />} intent="primary">
        Loading outlined
      </Button>
      <Button outlined icon={<Icon name="cancel" />} disabled intent="danger">
        Disabled outlined, danger
      </Button>
      <Button outlined icon={<Icon name="cancel" />} loading intent="danger">
        Loading outlined, danger
      </Button>
    </Group>
  );
};

export const Truncation = () => {
  return (
    <Group direction="column" spacing={8}>
      <Button>Normal</Button>
      <Button style={{maxWidth: '250px'}}>Normal with max-width</Button>
      <Button style={{maxWidth: '250px'}}>
        Four score and seven years ago our fathers brought forth on this continent
      </Button>
    </Group>
  );
};

export const Joined = () => {
  return (
    <Group direction="column" spacing={8}>
      <JoinedButtons>
        <Button>Main Action</Button>
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
          <Button icon={<Icon name="expand_more" />}></Button>
        </Popover>
      </JoinedButtons>
      <JoinedButtons>
        <Button>Left</Button>
        <Button>Center</Button>
        <Button>Right</Button>
      </JoinedButtons>
      <JoinedButtons>
        <Button icon={<Icon name="star" />}>Left</Button>
        <Button icon={<Icon name="star" />}>Center</Button>
        <Button icon={<Icon name="star" />}>Right</Button>
      </JoinedButtons>
      <JoinedButtons>
        <Button rightIcon={<Icon name="wysiwyg" />}>Left</Button>
        <Button rightIcon={<Icon name="wysiwyg" />}>Center</Button>
        <Button rightIcon={<Icon name="wysiwyg" />}>Right</Button>
      </JoinedButtons>
      <JoinedButtons>
        <Button icon={<Icon name="cached" />}></Button>
        <Button icon={<Icon name="wysiwyg" />}></Button>
        <Button icon={<Icon name="close" />}></Button>
      </JoinedButtons>
    </Group>
  );
};

export function LoadingStates() {
  return (
    <Box flex={{direction: 'row', gap: 12}}>
      <Button loading icon={<Icon name="wysiwyg" />}>
        Test
      </Button>
      <Button loading icon={<Icon name="close" />} rightIcon={<Icon name="cached" />}>
        Test
      </Button>
      <Button loading rightIcon={<Icon name="wysiwyg" />}>
        Test
      </Button>
      <Button loading intent="primary">
        Test
      </Button>
      <Button loading intent="danger">
        Test
      </Button>
    </Box>
  );
}
