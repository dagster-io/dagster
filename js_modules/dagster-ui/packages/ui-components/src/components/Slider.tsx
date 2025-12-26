import * as RadixSlider from '@radix-ui/react-slider';
import * as React from 'react';

import {Colors} from './Color';
import styles from './css/Slider.module.css';

interface Props {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step: number;
  orientation?: 'horizontal' | 'vertical';
  trackColor?: string;
  rangeColor?: string;
  disabled?: boolean;
  name?: string;
}

export const Slider = (props: Props) => {
  const {
    value,
    onChange,
    min = 0,
    max = 100,
    step,
    orientation = 'horizontal',
    trackColor = Colors.backgroundGray(),
    rangeColor = Colors.accentGray(),
    disabled = false,
    name,
  } = props;

  const style = {
    '--slider-track-color': trackColor,
    '--slider-range-color': rangeColor,
  } as React.CSSProperties;

  return (
    <RadixSlider.Root
      className={styles.slider}
      style={style}
      value={[value]}
      onValueChange={([first]) => first !== undefined && onChange(first)}
      min={min}
      max={max}
      step={step}
      disabled={disabled}
      orientation={orientation}
      name={name}
    >
      <RadixSlider.Track className={styles.track}>
        <RadixSlider.Range className={styles.range} />
      </RadixSlider.Track>
      <RadixSlider.Thumb className={styles.thumb} />
    </RadixSlider.Root>
  );
};
