import React from 'react';
import cx from 'classnames';
import { AnchorHeading } from 'hooks/AnchorHeadings/reducer';

const OnThisPage: React.FC<{
  anchors: AnchorHeading[];
}> = ({ anchors }) => {
  const leftPadding = {
    h1: 'pl-3',
    h2: 'pl-3',
    h3: 'pl-6',
    h4: 'pl-9',
    h5: 'pl-15',
    h6: 'pl-18',
  };

  return (
    <div className="ml-8 pr-2 pt-2 w-1/4 hidden lg:block lg:relative">
      {anchors.length > 0 && (
        <div className="py-4 border-l border-gray-300 fixed">
          {anchors.map((anchor) => (
            <a
              key={anchor.href}
              href={anchor.href}
              className={`group flex items-center pr-3 py-1 text-xs leading-5 text-gray-600 hover:text-gray-900 hover:text-blue-600 focus:outline-none focus:bg-gray-100 transition ease-in-out duration-150 ${cx(
                anchor.element && leftPadding[anchor.element],
              )}`}
            >
              <span className="truncate">{anchor.title}</span>
            </a>
          ))}
        </div>
      )}
    </div>
  );
};

export default OnThisPage;
