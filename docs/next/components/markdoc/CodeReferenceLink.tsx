import {unpackText} from 'util/unpackText';
import {LATEST_VERSION} from 'util/version';

import React from 'react';

export const CodeReferenceLink = ({filePath, isInline, children}) => {
  const url = `https://github.com/dagster-io/dagster/tree/${LATEST_VERSION}/${filePath}`;

  if (isInline) {
    return <a href={url}>{unpackText(children)}</a>;
  } else {
    return (
      <div className="bg-primary-100 rounded flex item-center p-4">
        <div>
          <svg className="h-8 w-8 text-primary-900" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8.128 19.825a1.586 1.586 0 0 1-1.643-.117 1.543 1.543 0 0 1-.53-.662 1.515 1.515 0 0 1-.096-.837l.736-4.247-3.13-3a1.514 1.514 0 0 1-.39-1.569c.09-.271.254-.513.475-.698.22-.185.49-.306.776-.35L8.66 7.73l1.925-3.862c.128-.26.328-.48.577-.633a1.584 1.584 0 0 1 1.662 0c.25.153.45.373.577.633l1.925 3.847 4.334.615c.29.042.562.162.785.348.224.186.39.43.48.704a1.514 1.514 0 0 1-.404 1.58l-3.13 3 .736 4.247c.047.282.014.572-.096.837-.111.265-.294.494-.53.662a1.582 1.582 0 0 1-1.643.117l-3.865-2-3.865 2z" />
          </svg>
        </div>
        <div className="pl-4 pt-1">
          You can find the code for this example on <a href={url}>Github</a>
        </div>
      </div>
    );
  }
};
