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

export const WithAutocompleteTokens = {
  render: Template,
  args: {
    value: JSON.stringify(
      {
        message: 'Hello {{name}}, your job {{job_id}} is complete!',
        details: 'Type { inside a string to see autocomplete hints',
      },
      null,
      2,
    ),
    additionalAutocompleteTokens: [
      {
        name: 'job_id',
        description: 'The unique identifier of the job',
        example: 'job-12345',
      },
      {
        name: 'job_name',
        description: 'The name of the job',
        example: 'my_daily_pipeline',
      },
      {
        name: 'run_id',
        description: 'The run identifier',
        example: 'run-abc-123',
      },
      {
        name: 'name',
        description: 'User display name',
        example: 'John Doe',
      },
    ],
  },
};
