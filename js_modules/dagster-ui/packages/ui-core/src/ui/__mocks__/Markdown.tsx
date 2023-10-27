import * as React from 'react';

import {Markdown} from '../Markdown';

export const MarkdownMock: React.FC<React.ComponentProps<typeof Markdown>> = (props) => {
  return <>{props.children}</>;
};

// eslint-disable-next-line
export default MarkdownMock;
