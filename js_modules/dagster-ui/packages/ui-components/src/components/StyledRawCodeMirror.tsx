import * as React from 'react';

import {DagsterCodeMirrorStyle} from './DagsterCodeMirrorStyle';
import {RawCodeMirror} from './RawCodeMirror';

const makeThemeString = (theme: string[] = []) => [...theme, 'dagster'].join(' ');

interface ThemeProp {
  theme?: string[];
}

export const StyledRawCodeMirror = (
  props: React.ComponentProps<typeof RawCodeMirror> & ThemeProp,
) => {
  const {options, theme, ...rest} = props;
  return (
    <>
      <DagsterCodeMirrorStyle />
      <RawCodeMirror {...rest} options={{...options, theme: makeThemeString(theme)}} />
    </>
  );
};
