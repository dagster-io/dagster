import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {Button} from './Button';
import {Icon} from './Icon';
import {MenuItem} from './Menu';
import {Select} from './Select';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Select',
  component: Select,
} as Meta;

type Product = {
  productName: string;
};

export const Default = () => {
  const [active, setActive] = React.useState<Product | null>(null);

  const items = React.useMemo(() => {
    const items = new Array(10).fill(null).map(() => ({productName: faker.commerce.productName()}));
    return Array.from(new Set(items));
  }, []);

  return (
    <Select<Product>
      items={items}
      itemPredicate={(query, item) => item.productName.toLowerCase().includes(query)}
      itemRenderer={(item, props) => (
        <MenuItem key={item.productName} text={item.productName} onClick={props.handleClick} />
      )}
      onItemSelect={(item) => setActive(item)}
    >
      <Button intent="primary" rightIcon={<Icon name="arrow_drop_down" />}>
        {active ? active.productName : 'Choose a product'}
      </Button>
    </Select>
  );
};
