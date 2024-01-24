import {Meta} from '@storybook/react';
import CodeMirror from 'codemirror';
import {useCallback, useMemo, useState} from 'react';

import {StyledRawCodeMirror} from '../StyledRawCodeMirror';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'StyledRawCodeMirror',
  component: StyledRawCodeMirror,
} as Meta;

export const Default = () => {
  const [value, setValue] = useState('');
  const onChange = useCallback((editor: CodeMirror.Editor) => {
    setValue(editor.getValue());
  }, []);

  const onReady = useCallback((editor: CodeMirror.Editor) => {
    console.log('Ready!', editor);
  }, []);

  const options = useMemo(
    () => ({
      lineNumbers: true,
      readOnly: false,
    }),
    [],
  );

  const handlers = useMemo(
    () => ({
      onChange,
      onReady,
    }),
    [onChange, onReady],
  );

  return <StyledRawCodeMirror value={value} options={options} handlers={handlers} />;
};

export const ReadOnly = () => {
  const options = useMemo(
    () => ({
      lineNumbers: true,
      readOnly: true,
    }),
    [],
  );

  return <StyledRawCodeMirror value={`hello\n  world`} options={options} />;
};
