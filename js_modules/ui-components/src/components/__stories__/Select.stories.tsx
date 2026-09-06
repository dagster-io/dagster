import faker from 'faker';
import {useMemo, useState} from 'react';

import {Box} from '../Box';
import {Button} from '../Button';
import {Icon} from '../Icon';
import {MenuItem} from '../Menu';
import {Select} from '../Select';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Select',
  component: Select,
};

type Product = {
  productName: string;
};

export const Default = () => {
  const [active, setActive] = useState<Product | null>(null);

  const items = useMemo(() => {
    const items = new Array(10).fill(null).map(() => ({productName: faker.commerce.productName()}));
    return Array.from(new Set(items));
  }, []);

  return (
    <Select<Product>
      items={items}
      itemPredicate={(query, item) => item.productName.toLowerCase().includes(query)}
      itemRenderer={(item, props) => (
        <MenuItem
          key={item.productName}
          text={item.productName}
          active={props.modifiers.active}
          onClick={props.handleClick}
        />
      )}
      onItemSelect={(item) => setActive(item)}
    >
      <Button intent="primary" rightIcon={<Icon name="arrow_drop_down" />}>
        {active ? active.productName : 'Choose a product'}
      </Button>
    </Select>
  );
};

export const WithMinWidth = () => {
  const [active, setActive] = useState<Product | null>(null);

  const items = useMemo(() => {
    const items = new Array(10).fill(null).map(() => ({productName: faker.commerce.productName()}));
    return Array.from(new Set(items));
  }, []);

  return (
    <Select<Product>
      items={items}
      itemPredicate={(query, item) => item.productName.toLowerCase().includes(query)}
      itemRenderer={(item, props) => (
        <MenuItem
          key={item.productName}
          text={item.productName}
          active={props.modifiers.active}
          onClick={props.handleClick}
        />
      )}
      onItemSelect={(item) => setActive(item)}
    >
      <Button
        intent="primary"
        style={{minWidth: '200px', display: 'flex', justifyContent: 'space-between'}}
        rightIcon={<Icon name="arrow_drop_down" />}
      >
        {active ? active.productName : 'Choose a product'}
      </Button>
    </Select>
  );
};

export const NonFilterable = () => {
  const [active, setActive] = useState<Product | null>(null);

  const items = useMemo(() => {
    const items = new Array(10).fill(null).map(() => ({productName: faker.commerce.productName()}));
    return Array.from(new Set(items));
  }, []);

  return (
    <Select<Product>
      filterable={false}
      items={items}
      itemRenderer={(item, props) => (
        <MenuItem
          key={item.productName}
          text={item.productName}
          active={props.modifiers.active}
          onClick={props.handleClick}
        />
      )}
      onItemSelect={(item) => setActive(item)}
    >
      <Button intent="primary" rightIcon={<Icon name="arrow_drop_down" />}>
        {active ? active.productName : 'Choose a product'}
      </Button>
    </Select>
  );
};

export const WithPositionBottomRight = () => {
  const [active, setActive] = useState<Product | null>(null);

  const items = useMemo(() => {
    const items = new Array(10).fill(null).map(() => ({productName: faker.commerce.productName()}));
    return Array.from(new Set(items));
  }, []);

  return (
    <Box flex={{justifyContent: 'flex-end'}}>
      <Select<Product>
        items={items}
        itemPredicate={(query, item) => item.productName.toLowerCase().includes(query)}
        itemRenderer={(item, props) => (
          <MenuItem
            key={item.productName}
            text={item.productName}
            active={props.modifiers.active}
            onClick={props.handleClick}
          />
        )}
        onItemSelect={(item) => setActive(item)}
        popoverProps={{position: 'bottom-right'}}
      >
        <Button intent="primary" rightIcon={<Icon name="arrow_drop_down" />}>
          {active ? active.productName : 'Choose a product'}
        </Button>
      </Select>
    </Box>
  );
};

export const WithFill = () => {
  const [active, setActive] = useState<Product | null>(null);

  const items = useMemo(() => {
    const items = new Array(10).fill(null).map(() => ({productName: faker.commerce.productName()}));
    return Array.from(new Set(items));
  }, []);

  return (
    <Box style={{width: 400}}>
      <Select<Product>
        fill
        items={items}
        itemPredicate={(query, item) => item.productName.toLowerCase().includes(query)}
        itemRenderer={(item, props) => (
          <MenuItem
            key={item.productName}
            text={item.productName}
            active={props.modifiers.active}
            onClick={props.handleClick}
          />
        )}
        onItemSelect={(item) => setActive(item)}
      >
        <Button
          intent="primary"
          rightIcon={<Icon name="arrow_drop_down" />}
          style={{width: '100%', display: 'flex', justifyContent: 'space-between'}}
        >
          {active ? active.productName : 'Choose a product'}
        </Button>
      </Select>
    </Box>
  );
};
