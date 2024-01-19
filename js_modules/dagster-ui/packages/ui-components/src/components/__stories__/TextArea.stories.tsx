import {Meta} from '@storybook/react';
import {useState} from 'react';

import {Colors} from '../Color';
import {TextArea} from '../TextInput';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TextArea',
  component: TextArea,
} as Meta;

export const Default = () => {
  const [value, setValue] = useState('');
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
  const [value, setValue] = useState('');
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
  const [value, setValue] = useState('');
  return (
    <TextArea
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      $resize="none"
      $strokeColor={Colors.accentRed()}
    />
  );
};
