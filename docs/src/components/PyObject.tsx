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

  let href = `/api/dagster/${section}#${module}.${object}`;
  if (section === 'libraries' || section === 'dagster_dg') {
    const _package = module.replace(/_/g, '-');
    href = `/api/${section}/${_package}#${module}.${object}`;
  }

  return (
    <Link href={href}>
      <code style={{paddingLeft: '4px', paddingRight: '4px'}}>{textValue}</code>
    </Link>
  );
};
