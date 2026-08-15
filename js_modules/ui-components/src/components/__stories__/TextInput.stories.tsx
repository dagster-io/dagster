import {useState} from 'react';

import {Box} from '../Box';
import {Button} from '../Button';
import {Colors} from '../Color';
import {Icon} from '../Icon';
import {TextInput} from '../TextInput';
import {Text} from '../Typography';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TextInput',
  component: TextInput,
};

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

export const Disabled = () => {
  return (
    <Box flex={{direction: 'column', gap: 8}} style={{width: '300px'}}>
      <TextInput icon="layers" placeholder="Disabled input…" value="" disabled />
      <TextInput icon="layers" placeholder="Enabled input…" value="" />
    </Box>
  );
};

export const PasswordManagers = () => {
  const [value, setValue] = useState('');
  return (
    <Box flex={{direction: 'column', gap: 8}} style={{width: '300px'}}>
      <label htmlFor="username">
        <Box flex={{direction: 'column', gap: 4}}>
          <Text size={12}>Username</Text>
          <TextInput
            name="username-1"
            placeholder="Password managers allowed…"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            allowPasswordManagers
          />
        </Box>
      </label>
      <label htmlFor="password">
        <Box flex={{direction: 'column', gap: 4}}>
          <Text size={12}>Username (no password managers)</Text>
          <TextInput
            name="username-2"
            placeholder="Password managers not allowed…"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        </Box>
      </label>
    </Box>
  );
};
