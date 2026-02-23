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
