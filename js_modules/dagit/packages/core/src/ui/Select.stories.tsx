import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {ButtonWIP} from './Button';
import {IconWIP} from './Icon';
import {MenuItemWIP} from './Menu';
import {SelectWIP as Select} from './Select';

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
        <MenuItemWIP key={item.productName} text={item.productName} onClick={props.handleClick} />
      )}
      onItemSelect={(item) => setActive(item)}
    >
      <ButtonWIP intent="primary" rightIcon={<IconWIP name="arrow_drop_down" />}>
        {active ? active.productName : 'Choose a product'}
      </ButtonWIP>
    </Select>
  );
};
