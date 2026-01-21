import * as React from 'react';

import {StyledJSONEditor, StyledJSONEditorProps} from '../StyledJSONEditor';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Components/StyledJSONEditor',
  component: StyledJSONEditor,
};

const Template = (args: StyledJSONEditorProps) => {
  const [value, setValue] = React.useState(args.value);
  return (
    <div style={{height: '300px', width: '100%'}}>
      <StyledJSONEditor
        {...args}
        value={value}
        onChange={(newValue) => {
          setValue(newValue);
          args.onChange?.(newValue);
        }}
      />
    </div>
  );
};

export const Default = {
  render: Template,
  args: {
    value: JSON.stringify({hello: 'world', foo: [1, 2, 3]}, null, 2),
  },
};

export const ReadOnly = {
  render: Template,
  args: {
    value: JSON.stringify({read: 'only', static: true}, null, 2),
    options: {readOnly: true},
  },
};

export const CustomTheme = {
  render: Template,
  args: {
    value: JSON.stringify({theme: 'custom', dark: true}, null, 2),
    theme: ['my-custom-theme'], // Assuming 'my-custom-theme' exists or just showing prop usage
  },
};

export const WithValidation = {
  render: Template,
  args: {
    value: '{\n  "broken": "json",\n',
  },
};
