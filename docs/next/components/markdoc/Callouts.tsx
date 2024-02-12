// import * as React from 'react';

import Icons from '../Icons';

const ADMONITION_STYLES = {
  note: {
    colors: {
      bg: 'primary-100',
      borderIcon: 'primary-500',
      text: 'gray-900',
    },
    icon: Icons.About,
  },
  warning: {
    colors: {bg: 'yellow-50', borderIcon: 'yellow-400', text: 'yellow-700'},
    icon: Icons.About,
  },
};
const Admonition = ({style, children}) => {
  const {colors, icon} = ADMONITION_STYLES[style];
  return (
    <div className={`bg-${colors.bg} border-l-4 border-${colors.borderIcon} px-4 my-4`}>
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <svg
            className={`h-5 w-5 text-${colors.borderIcon}`}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 25 25"
            fill="currentColor"
            aria-hidden="true"
          >
            {icon && icon}
          </svg>
        </div>
        <div className="ml-3">
          <span className={`text-sm text-${colors.text}`}>{children}</span>
        </div>
      </div>
    </div>
  );
};

export const Note = ({children}) => {
  return <Admonition style="note">{children}</Admonition>;
};

export const Warning = ({children}) => {
  return <Admonition style="warning">{children}</Admonition>;
};
