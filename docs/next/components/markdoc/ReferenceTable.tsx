import {unpackText} from 'util/unpackText';

import React from 'react';

export const ReferenceTable = ({children}) => {
  return (
    <table
      className="table"
      style={{
        width: '100%',
      }}
    >
      <thead>
        <tr>
          <th>Property</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>{children}</tbody>
    </table>
  );
};

export const ReferenceTableItem = ({propertyName, children}) => {
  return (
    <tr>
      <td
        style={{
          width: '40%',
        }}
      >
        {propertyName}
      </td>
      <td>{unpackText(children)}</td>
    </tr>
  );
};
