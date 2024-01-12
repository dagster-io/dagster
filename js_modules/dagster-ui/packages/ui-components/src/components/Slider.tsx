// eslint-disable-next-line no-restricted-imports
import {
  Slider as BlueprintSlider,
  MultiSlider as BlueprintMultiSlider,
  SliderProps as BlueprintSliderProps,
  MultiSliderProps as BlueprintMultiSliderProps,
} from '@blueprintjs/core';
import * as React from 'react';
import styled, {css} from 'styled-components';

import {Colors} from './Color';

interface SliderProps extends BlueprintSliderProps {
  fillColor?: string;
}

export const Slider = ({fillColor = Colors.accentGray(), ...rest}: SliderProps) => {
  return <StyledSlider {...rest} intent="none" $fillColor={fillColor} />;
};

interface MultiSliderProps extends BlueprintMultiSliderProps {
  fillColor?: string;
  children: React.ReactNode;
}

export const MultiSlider = ({fillColor = Colors.accentGray(), ...rest}: MultiSliderProps) => {
  return <StyledMultiSlider {...rest} intent="none" $fillColor={fillColor} />;
};

MultiSlider.Handle = BlueprintMultiSlider.Handle;

export const SliderStyles = css<{$fillColor: string}>`
  .bp4-slider-track {
    height: 8px;
    .bp4-slider-progress {
      background-color: ${(p) => p.$fillColor};
      opacity: 0.4;
      height: 8px;
    }
    .bp4-slider-progress.bp4-intent-primary {
      background-color: ${(p) => p.$fillColor};
      opacity: 1;
      height: 8px;
    }
  }
  &.bp4-vertical {
    width: 20px;
    min-width: 20px;
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
    border: 2px solid ${Colors.accentGray()};
    background: ${Colors.backgroundLighter()};
    box-shadow: none;
    &:hover {
      border: 2px solid ${Colors.accentGrayHover()};
      box-shadow: ${Colors.shadowDefault()} 0px 2px 12px 0px;
    }

    .bp4-slider-label {
      background: ${Colors.accentBlue()};
      box-shadow: 0 1px 4px ${Colors.shadowDefault()};
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
