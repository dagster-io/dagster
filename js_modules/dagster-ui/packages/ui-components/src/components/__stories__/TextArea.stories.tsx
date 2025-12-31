import {useState} from 'react';

import {Colors} from '../Color';
import {TextArea} from '../TextArea';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TextArea',
  component: TextArea,
};

export const Default = () => {
  const [value, setValue] = useState('');
  return (
    <TextArea
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      resize="none"
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
      resize="vertical"
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
      resize="none"
      strokeColor={Colors.accentRed()}
    />
  );
};

export const Disabled = () => {
  const [value, setValue] = useState('This textarea is disabled');
  return (
    <TextArea
      placeholder="Type anything…"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      resize="vertical"
      disabled
    />
  );
};
