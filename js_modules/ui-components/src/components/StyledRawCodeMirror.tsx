import * as React from 'react';

import {DagsterCodeMirrorStyle} from './DagsterCodeMirrorStyle';
import {RawCodeMirror} from './RawCodeMirror';
import {registerYaml} from './configeditor/codemirror-yaml/mode';

// Explicitly register YAML to ensure that the YAML import is bundled correctly.
registerYaml();

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
