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
  displayText?: string;
  pluralize?: boolean;
  decorator?: boolean;
}> = ({section, object, displayText, module = 'dagster', pluralize = false, decorator = false}) => {
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

  // Libraries are in a sub-folder, and the `href` will need to be structured slightly differently
  //
  //     /api/python-api/assets#dagster.asset
  //     /api/python-api/libraries/dagster-snowflake#dagster_snowflake.SnowflakeConnection
  //
  let href = `/api/python-api/${section}#${module}.${object}`;
  if (section === 'libraries') {
    const _package = module.replace(/_/g, '-');
    href = `/api/python-api/libraries/${_package}#${module}.${object}`;
  }

  console.log('->', href);

  return (
    <Link href={href}>
      <code style={{paddingLeft: '4px', paddingRight: '4px'}}>{textValue}</code>
    </Link>
  );
};
