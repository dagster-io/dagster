import {Meta} from '@storybook/react';
import * as React from 'react';

import {Colors} from '../Colors';
import {TextArea} from '../TextInput';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TextArea',
  component: TextArea,
} as Meta;

export const Default = () => {
  const [value, setValue] = React.useState('');
  return (
    <TextArea
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      $resize="none"
    />
  );
};

export const Resize = () => {
  const [value, setValue] = React.useState('');
  return (
    <TextArea
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      $resize="vertical"
    />
  );
};

export const StrokeColor = () => {
  const [value, setValue] = React.useState('');
  return (
    <TextArea
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      $resize="none"
      $strokeColor={Colors.Red500}
    />
  );
};
