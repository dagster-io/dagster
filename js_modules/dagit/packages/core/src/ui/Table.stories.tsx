import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Table} from './Table';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Table',
  component: Table,
} as Meta;

export const Basics = () => {
  return (
    <Table>
      <thead>
        <tr>
          <th>State</th>
          <th>Capital</th>
          <th>Largest city</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>California</td>
          <td>Sacramento</td>
          <td>Los Angeles</td>
        </tr>
        <tr>
          <td>Illinois</td>
          <td>Springfield</td>
          <td>Chicago</td>
        </tr>
        <tr>
          <td>Minnesota</td>
          <td>St. Paul</td>
          <td>Minneapolis</td>
        </tr>
        <tr>
          <td>North Carolina</td>
          <td>Raleigh</td>
          <td>Charlotte</td>
        </tr>
        <tr>
          <td>Texas</td>
          <td>Austin</td>
          <td>Houston</td>
        </tr>
        <tr>
          <td>Virginia</td>
          <td>Richmond</td>
          <td>Virginia Beach</td>
        </tr>
      </tbody>
    </Table>
  );
};
