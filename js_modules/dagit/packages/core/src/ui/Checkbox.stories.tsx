import {Colors, H4} from '@blueprintjs/core';
import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';
import {useState} from 'react';

import {Checkbox} from './Checkbox';
import {ColorsWIP} from './Colors';
import {Group} from './Group';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Checkbox',
  component: Checkbox,
} as Meta;

export const Default = () => {
  const [state, setState] = useState<'true' | 'false' | 'indeterminate'>('false');
  const onChange = () =>
    setState(({true: 'indeterminate', indeterminate: 'false', false: 'true'} as const)[state]);

  return (
    <Group spacing={8} direction="column">
      {[ColorsWIP.Blue500, ColorsWIP.ForestGreen, ColorsWIP.Gray800].map((fillColor) => (
        <Group spacing={24} direction="row" key={fillColor}>
          <Checkbox
            label="Hello world"
            checked={state === 'false' ? false : true}
            indeterminate={state === 'indeterminate'}
            fillColor={fillColor}
            onChange={onChange}
            format="check"
          />
          <Checkbox
            label="Hello world"
            checked={state === 'false' ? false : true}
            indeterminate={state === 'indeterminate'}
            fillColor={fillColor}
            onChange={onChange}
            format="star"
          />
          <Checkbox
            label="Hello world"
            checked={state === 'false' ? false : true}
            indeterminate={state === 'indeterminate'}
            fillColor={fillColor}
            onChange={onChange}
            format="switch"
          />
        </Group>
      ))}
      <Group spacing={24} direction="row">
        <Checkbox
          disabled
          label="Hello world"
          checked={state === 'false' ? false : true}
          indeterminate={state === 'indeterminate'}
          onChange={onChange}
          format="check"
        />
        <Checkbox
          disabled
          label="Hello world"
          checked={state === 'false' ? false : true}
          indeterminate={state === 'indeterminate'}
          onChange={onChange}
          format="star"
        />
        <Checkbox
          disabled
          label="Hello world"
          checked={state === 'false' ? false : true}
          indeterminate={state === 'indeterminate'}
          onChange={onChange}
          format="switch"
        />
      </Group>
    </Group>
  );
};
