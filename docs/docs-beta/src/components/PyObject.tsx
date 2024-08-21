import React from 'react';
import Link from '@docusaurus/Link';
export const SearchIndexContext = React.createContext(null);

export const PyObject: React.FunctionComponent<{
  module: string;
  object: string;
  method?: string;
  displayText?: string;
  pluralize?: boolean;
  decorator?: boolean;
}> = ({object, method, displayText, pluralize = false, decorator = false}) => {
  let textValue = displayText || object;
  if (pluralize) {
    textValue += 's';
  }
  if (decorator) {
    textValue = '@' + textValue;
  }
  if (method) {
    textValue += '.' + method;
  }

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    alert('PyObject not implemented yet');
  };

  return (
    <Link
      href="#"
      onClick={handleClick}
      className="pyobject underline cursor-pointer"
      title="PyObject not implemented yet"
    >
      <code>{textValue}</code>
    </Link>
  );
};
