import * as React from 'react';

import {StyledJSONEditor} from '../StyledJSONEditor';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'StyledJSONEditor',
  component: StyledJSONEditor,
};

export const Default = () => {
  const [value, setValue] = React.useState('{"hello": "world"}');
  return (
    <div style={{height: 300}}>
      <StyledJSONEditor value={value} onChange={setValue} />
    </div>
  );
};

export const Jinja2 = () => {
  const [value, setValue] = React.useState(
    'Hello {{ name }},\n{% if active %}\n  Welcome back!\n{% endif %}',
  );
  return (
    <div style={{height: 300}}>
      <StyledJSONEditor value={value} onChange={setValue} />
    </div>
  );
};

export const PlainText = () => {
  const [value, setValue] = React.useState('Hello world');
  return (
    <div style={{height: 300}}>
      <StyledJSONEditor value={value} onChange={setValue} />
    </div>
  );
};
