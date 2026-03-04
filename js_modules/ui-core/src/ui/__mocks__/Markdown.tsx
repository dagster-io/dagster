import * as React from 'react';

import {Markdown} from '../Markdown';

export const MarkdownMock = (props: React.ComponentProps<typeof Markdown>) => {
  return <>{props.children}</>;
};

// eslint-disable-next-line
export default MarkdownMock;
