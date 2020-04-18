import React from 'react';
import cx from 'classnames';
import { AnchorHeading } from 'hooks/AnchorHeadings/reducer';

const OnThisPage: React.FC<{
  anchors: AnchorHeading[];
}> = ({ anchors }) => {
  return (
    <div className="px-2 pt-2 w-64 hidden md:block">
      <h3 className="px-3 text-xs leading-4 font-semibold text-gray-500 uppercase tracking-wider">
        On This Page
      </h3>
      <div className="mt-1">
        {anchors.map((anchor) => (
          <a
            key={anchor.href}
            href={anchor.href}
            className={`group flex items-center pr-3 py-2 text-sm leading-5 font-medium text-gray-600 rounded-md hover:text-gray-900 hover:bg-gray-50 focus:outline-none focus:bg-gray-100 transition ease-in-out duration-150 ${cx(
              {
                'pl-3': anchor.element === 'h1',
              },
              {
                'pl-6': anchor.element === 'h2',
              },
              {
                'pl-9': anchor.element === 'h3',
              },
              {
                'pl-15': anchor.element === 'h4',
              },
              {
                'pl-18': anchor.element === 'h5',
              },
              {
                'pl-21': anchor.element === 'h6',
              },
            )}`}
          >
            <span className="truncate">{anchor.title}</span>
          </a>
        ))}
      </div>
    </div>
  );
};

export default OnThisPage;
