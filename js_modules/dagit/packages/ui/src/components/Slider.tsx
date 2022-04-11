// eslint-disable-next-line no-restricted-imports
import {
  Slider as BlueprintSlider,
  MultiSlider as BlueprintMultiSlider,
  SliderProps,
  MultiSliderProps,
} from '@blueprintjs/core';
import * as React from 'react';
import styled, {css} from 'styled-components/macro';

import {Colors} from './Colors';

export const Slider: React.FC<SliderProps & {fillColor?: string}> = ({
  fillColor = Colors.Gray600,
  ...rest
}) => {
  return <StyledSlider {...rest} intent="none" $fillColor={fillColor} />;
};

export const MultiSlider: React.FC<MultiSliderProps & {fillColor?: string}> & {
  Handle: typeof BlueprintMultiSlider.Handle;
} = ({fillColor = Colors.Gray600, ...rest}) => {
  return <StyledMultiSlider {...rest} intent="none" $fillColor={fillColor} />;
};

MultiSlider.Handle = BlueprintMultiSlider.Handle;

export const SliderStyles = css<{$fillColor: string}>`
  .bp3-slider-track {
    height: 8px;
    .bp3-slider-progress {
      background-color: ${(p) => p.$fillColor};
      opacity: 0.2;
      height: 8px;
    }
    .bp3-slider-progress.bp3-intent-primary {
      background-color: ${(p) => p.$fillColor};
      opacity: 1;
      height: 8px;
    }
  }
  &.bp3-vertical .bp3-slider-track,
  &.bp3-vertical .bp3-slider-track .bp3-slider-progress {
    height: initial;
    width: 8px;
  }
  .bp3-slider-handle {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: 2px solid ${Colors.Gray300};
    background: ${Colors.White};
    box-shadow: none;
    &:hover {
      border: 2px solid ${Colors.Gray400};
      box-shadow: rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;
    }

    .bp3-slider-label {
      background: ${Colors.Gray900};
      box-shadow: 0 1px 4px rgba(0,0,0,0.15)
      padding: 4px 8px;
    }
  }
`;

const StyledMultiSlider = styled(BlueprintMultiSlider)<{$fillColor: string}>`
  ${SliderStyles}
`;
const StyledSlider = styled(BlueprintSlider)<{$fillColor: string}>`
  ${SliderStyles}
`;
