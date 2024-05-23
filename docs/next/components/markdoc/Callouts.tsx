import * as React from 'react';

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

const applyTextStyles = (children, colors) => {
  return React.Children.map(children, (child) => {
    const existingStyles = child.props.className || '';
    const newStyles = `text-sm text-${colors.text} ${existingStyles}`;
    return React.cloneElement(child, {className: newStyles});
  });
};

const Admonition = ({style, children}) => {
  const {colors, icon} = ADMONITION_STYLES[style];
  return (
    <div className={`bg-${colors.bg} border-l-4 border-${colors.borderIcon} p-4 my-4`}>
      <div className="flex">
        {/* Make container for the svg element that aligns it with the top right of the parent flex container */}
        <div className="flex-shrink-0">
          <svg
            className={`mt-.5 h-5 w-5 text-${colors.borderIcon}`}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 25 25"
            fill="currentColor"
            aria-hidden="true"
          >
            {icon && icon}
          </svg>
        </div>
        <div className="flex-shrink-1 ml-3">
          <div className="admonition"> {applyTextStyles(children, colors)} </div>
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
