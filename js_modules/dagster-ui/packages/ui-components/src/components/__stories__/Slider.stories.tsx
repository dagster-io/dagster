// eslint-disable-next-line no-restricted-imports
import {Intent} from '@blueprintjs/core';
import {useState} from 'react';

import {Colors} from '../Color';
import {Group} from '../Group';
import {MultiSlider, Slider} from '../Slider';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Slider',
  component: Slider,
};

export const Sizes = () => {
  const [value, setValue] = useState(2);
  const [minValue, setMinValue] = useState(1);

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
          const [first] = values;
          if (typeof first === 'number') {
            setValue(first);
          }
        }}
      >
        <MultiSlider.Handle value={value} type="full" intentAfter={Intent.PRIMARY} />
      </MultiSlider>

      <MultiSlider
        min={0}
        max={10}
        stepSize={0.01}
        fillColor={Colors.accentBlue()}
        labelRenderer={(value: number) => (
          <span style={{whiteSpace: 'nowrap'}}>Value: {value.toFixed(1)}</span>
        )}
        onChange={(values: number[]) => {
          const [first, second] = values;
          if (typeof first === 'number' && typeof second === 'number') {
            setMinValue(Math.min(first, second));
            setValue(Math.max(first, second));
          }
        }}
      >
        <MultiSlider.Handle value={minValue} type="full" intentAfter={Intent.PRIMARY} />
        <MultiSlider.Handle value={value} type="full" intentBefore={Intent.PRIMARY} />
      </MultiSlider>
    </Group>
  );
};
