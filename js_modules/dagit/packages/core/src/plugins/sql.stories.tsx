import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {IPluginSidebarProps} from '../plugins';

import {SidebarComponent as SQLDialogComponent} from './sql';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'SQL Dialog Component',
  component: SQLDialogComponent,
} as Meta;

const props: IPluginSidebarProps = {
  definition: {
    name: 'Important Stuff',
    metadata: [
      {
        key: 'sql',
        value: `SELECT
  DATE_FORMAT(order_date, '%Y-%m-%d') AS order_day,
  COUNT(*) AS num_orders
    FROM cust_order
    GROUP BY DATE_FORMAT(order_date, '%Y-%m-%d')
    ORDER BY order_date ASC;`,
      },
    ],
  },
};

export const ButtonAndDialog = () => {
  return <SQLDialogComponent {...props} />;
};
