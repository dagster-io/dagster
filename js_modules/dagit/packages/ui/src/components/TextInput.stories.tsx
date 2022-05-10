import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Colors} from './Colors';
import {Icon} from './Icon';
import {TextInput} from './TextInput';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TextInput',
  component: TextInput,
} as Meta;

export const Default = () => {
  const [value, setValue] = React.useState('');
  return (
    <TextInput
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
    />
  );
};

export const WithIcon = () => {
  const [value, setValue] = React.useState('');
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
  const [value, setValue] = React.useState('');
  return (
    <TextInput
      icon="layers"
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      strokeColor={Colors.Red500}
    />
  );
};

export const RightElement = () => {
  const [value, setValue] = React.useState('');
  return (
    <TextInput
      icon="layers"
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      rightElement={<Icon name="info" color={Colors.Gray500} />}
    />
  );
};
