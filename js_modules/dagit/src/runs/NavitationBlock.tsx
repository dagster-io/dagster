import * as React from 'react';
import {Prompt} from 'react-router-dom';

import {useOnBeforeUnload} from 'src/hooks/useOnBeforeUnload';

interface Props {
  message: string;
}

export const NavigationBlock = (props: Props) => {
  useOnBeforeUnload();
  return <Prompt message={props.message} />;
};
