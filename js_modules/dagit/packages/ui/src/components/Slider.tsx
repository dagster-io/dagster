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

export const MultiSlider: React.FC<
  MultiSliderProps & {fillColor?: string; children: React.ReactNode}
> & {
  Handle: typeof BlueprintMultiSlider.Handle;
} = ({fillColor = Colors.Gray600, ...rest}) => {
  return <StyledMultiSlider {...rest} intent="none" $fillColor={fillColor} />;
};

MultiSlider.Handle = BlueprintMultiSlider.Handle;

export const SliderStyles = css<{$fillColor: string}>`
  .bp4-slider-track {
    height: 8px;
    .bp4-slider-progress {
      background-color: ${(p) => p.$fillColor};
      opacity: 0.2;
      height: 8px;
    }
    .bp4-slider-progress.bp4-intent-primary {
      background-color: ${(p) => p.$fillColor};
      opacity: 1;
      height: 8px;
    }
  }
  &.bp4-vertical .bp4-slider-track,
  &.bp4-vertical .bp4-slider-track .bp4-slider-progress {
    height: initial;
    width: 8px;
  }
  .bp4-slider-handle {
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

    .bp4-slider-label {
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
