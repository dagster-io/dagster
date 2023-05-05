import {Meta} from '@storybook/react';
import * as React from 'react';

import {ButtonGroup} from '../ButtonGroup';
import {ProductTour, ProductTourPosition as Position} from '../ProductTour';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'ProductTour',
  component: ProductTour,
} as Meta;

export const Positions = () => {
  const [activeItem, setActiveItem] = React.useState(Position.TOP_LEFT);
  const active = React.useMemo(() => new Set([activeItem]), [activeItem]);
  return (
    <>
      <ButtonGroup
        activeItems={active}
        buttons={[
          ['Position.TOP_LEFT', Position.TOP_LEFT],
          ['Position.TOP_CENTER', Position.TOP_CENTER],
          ['Position.TOP_RIGHT', Position.TOP_RIGHT],
          ['Position.BOTTOM_LEFT', Position.BOTTOM_LEFT],
          ['Position.BOTTOM_CENTER', Position.BOTTOM_CENTER],
          ['Position.BOTTOM_RIGHT', Position.BOTTOM_RIGHT],
        ].map(([str, value]) => ({label: str, id: value as Position}))}
        onClick={(pos: Position) => setActiveItem(pos)}
      />
      <div
        style={{
          paddingTop: '400px',
          height: '2000px',
          justifyContent: 'space-around',
          display: 'flex',
        }}
      >
        <ProductTour
          title="My product tour"
          description={
            <span>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam gravida tortor sed
              odio cursus vehicula. Vestibulum ultricies placerat massa, eu consequat quam gravida
              quis. Donec sodales erat id leo accumsan rutrum.
            </span>
          }
          position={activeItem}
          img="https://dagster.io/_next/image?url=%2Fimages-2022-july%2Fserverless.png&w=3840&q=75"
          actions={{
            dismiss: () => {},
            next: () => {},
          }}
        >
          <div
            style={{
              padding: '32px',
              border: '1px solid red',
              background: 'red',
            }}
          />
        </ProductTour>
      </div>
    </>
  );
};
