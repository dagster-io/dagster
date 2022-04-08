// eslint-disable-next-line no-restricted-imports
import {Intent} from '@blueprintjs/core';
import {MultiSlider} from '@dagster-io/ui';
import moment from 'moment-timezone';
import React from 'react';
import styled from 'styled-components/macro';

export const SliceSlider: React.FC<{
  maxUnix: number;
  minUnix: number;
  value: number;
  disabled: boolean;
  onChange: (val: number) => void;
}> = ({minUnix, maxUnix, value, disabled, onChange}) => {
  const delta = maxUnix - minUnix;
  const timeout = React.useRef<NodeJS.Timeout>();

  return (
    <div style={{width: 160}} onClick={(e) => e.stopPropagation()}>
      <SliderWithHandleLabelOnly
        min={0}
        max={1}
        disabled={disabled}
        stepSize={0.01}
        labelRenderer={(value: number) => (
          <span style={{whiteSpace: 'nowrap'}}>
            Run Start &gt; {moment.unix(delta * value + minUnix).format('YYYY-MM-DD')}
          </span>
        )}
        onChange={(values: number[]) => {
          if (timeout.current) {
            clearTimeout(timeout.current);
          }
          timeout.current = setTimeout(() => onChange(delta * values[0] + minUnix), 10);
        }}
      >
        <MultiSlider.Handle
          value={(value - minUnix) / delta}
          type="full"
          intentAfter={Intent.PRIMARY}
        />
      </SliderWithHandleLabelOnly>
    </div>
  );
};

const SliderWithHandleLabelOnly = styled(MultiSlider)`
  &.bp3-slider {
    height: 19px;
  }
  .bp3-slider-axis > .bp3-slider-label {
    display: none;
  }
  .bp3-slider-handle > .bp3-slider-label {
    display: none;
  }
  .bp3-slider-handle.bp3-active > .bp3-slider-label {
    display: initial;
  }
`;
