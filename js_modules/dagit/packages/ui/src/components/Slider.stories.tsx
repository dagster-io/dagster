import {Intent} from '@blueprintjs/core';
import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {ColorsWIP} from './Colors';
import {Group} from './Group';
import {Slider, MultiSlider} from './Slider';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Slider',
  component: Slider,
} as Meta;

export const Sizes = () => {
  const [value, setValue] = React.useState(2);
  const [minValue, setMinValue] = React.useState(1);

  return (
    <Group direction="column" spacing={32}>
      <Slider value={value} onChange={setValue} max={10} labelStepSize={2} />

      <Slider
        vertical
        min={0}
        max={10}
        stepSize={1}
        value={value}
        labelRenderer={false}
        onChange={setValue}
      />

      <MultiSlider
        min={0}
        max={10}
        stepSize={0.1}
        labelRenderer={(value: number) => (
          <span style={{whiteSpace: 'nowrap'}}>Value: {value.toFixed(1)}</span>
        )}
        onChange={(values: number[]) => {
          setValue(values[0]);
        }}
      >
        <MultiSlider.Handle value={value} type="full" intentAfter={Intent.PRIMARY} />
      </MultiSlider>

      <MultiSlider
        min={0}
        max={10}
        stepSize={0.01}
        fillColor={ColorsWIP.Blue500}
        labelRenderer={(value: number) => (
          <span style={{whiteSpace: 'nowrap'}}>Value: {value.toFixed(1)}</span>
        )}
        onChange={(values: number[]) => {
          setMinValue(Math.min(values[0], values[1]));
          setValue(Math.max(values[0], values[1]));
        }}
      >
        <MultiSlider.Handle value={minValue} type="full" intentAfter={Intent.PRIMARY} />
        <MultiSlider.Handle value={value} type="full" intentBefore={Intent.PRIMARY} />
      </MultiSlider>
    </Group>
  );
};
