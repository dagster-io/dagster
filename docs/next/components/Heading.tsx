import * as React from 'react';

export function Heading({id = '', level = 1, children, className}) {
  return React.createElement(
    `h${level}`,
    {
      id,
      className: ['heading', className].filter(Boolean).join(' '),
    },
    children,
    <a className="no-underline group" href={`#${id}`}>
      <span className="ml-2 text-gray-200 hover:text-gray-800 hover:underline">#</span>
    </a>,
  );
}
