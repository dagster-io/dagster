import * as React from 'react';

export function Heading({id = '', level = 1, children}) {
  return React.createElement(
    `h${level}`,
    {
      id,
    },
    children,
  );
}
