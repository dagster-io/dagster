import Link from '@docusaurus/Link';
import React from 'react';

export const SearchIndexContext = React.createContext(null);

/**
 * PyObject component renders a formatted link to the Python API docs.
 *
 * Because we are using the `<Link>` component, Docusaurus will validate broken links on build.
 */
export const PyObject: React.FunctionComponent<{
  section: string;
  module: string;
  object: string;
  method?: string;
  displayText?: string;
  pluralize?: boolean;
  decorator?: boolean;
}> = ({
  section,
  method,
  object,
  displayText,
  module = 'dagster',
  pluralize = false,
  decorator = false,
}) => {
  let textValue = displayText || object;
  if (pluralize) {
    textValue += 's';
  }
  if (decorator) {
    if (module === 'dagster') {
      textValue = '@dg.' + textValue;
    } else {
      textValue = '@' + module + '.' + textValue;
    }
  }
  if (method) {
    textValue += '.' + method;
  }

  // As we don't have access to the searchContext like we did in the Next.js version of docs, we
  // will instead require the user to explicitly define the `.rst` location of the module / object
  // via the `section` prop.
  //
  // For example: /api/python-api/assets#dagster.MaterializeResult
  const href = `/api/python-api/${section}#${module}.${object}`;

  return (
    <Link href={href}>
      <code style={{paddingLeft: '4px', paddingRight: '4px'}}>{textValue}</code>
    </Link>
  );
};
