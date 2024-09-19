import {Meta} from '@storybook/react';
import {useState} from 'react';

import {Box} from '../Box';
import {Button} from '../Button';
import {Colors} from '../Color';
import {Icon} from '../Icon';
import {TextInput} from '../TextInput';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TextInput',
  component: TextInput,
} as Meta;

export const Default = () => {
  const [value, setValue] = useState('');
  return (
    <TextInput
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
    />
  );
};

export const WithIcon = () => {
  const [value, setValue] = useState('');
  return (
    <TextInput
      icon="layers"
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
    />
  );
};

export const StrokeColor = () => {
  const [value, setValue] = useState('');
  return (
    <TextInput
      icon="layers"
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      strokeColor={Colors.accentRed()}
    />
  );
};

export const RightElement = () => {
  const [value, setValue] = useState('');
  return (
    <TextInput
      icon="layers"
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      rightElement={<Icon name="info" color={Colors.accentPrimary()} />}
    />
  );
};

export const NextToButton = () => {
  const [value, setValue] = useState('');
  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <TextInput
        icon="layers"
        placeholder="Type anything…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        rightElement={<Icon name="info" color={Colors.accentPrimary()} />}
      />
      <Button>Hello</Button>
    </Box>
  );
};
