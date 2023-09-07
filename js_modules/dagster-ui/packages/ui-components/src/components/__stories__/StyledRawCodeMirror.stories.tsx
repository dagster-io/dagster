import {Meta} from '@storybook/react';
import CodeMirror from 'codemirror';
import * as React from 'react';

import {StyledRawCodeMirror} from '../StyledRawCodeMirror';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'StyledRawCodeMirror',
  component: StyledRawCodeMirror,
} as Meta;

export const Default = () => {
  const [value, setValue] = React.useState('');
  const onChange = React.useCallback((editor: CodeMirror.Editor) => {
    setValue(editor.getValue());
  }, []);

  const onReady = React.useCallback((editor: CodeMirror.Editor) => {
    console.log('Ready!', editor);
  }, []);

  const options = React.useMemo(
    () => ({
      lineNumbers: true,
      readOnly: false,
    }),
    [],
  );

  const handlers = React.useMemo(
    () => ({
      onChange,
      onReady,
    }),
    [onChange, onReady],
  );

  return <StyledRawCodeMirror value={value} options={options} handlers={handlers} />;
};

export const ReadOnly = () => {
  const options = React.useMemo(
    () => ({
      lineNumbers: true,
      readOnly: true,
    }),
    [],
  );

  return <StyledRawCodeMirror value={`hello\n  world`} options={options} />;
};
