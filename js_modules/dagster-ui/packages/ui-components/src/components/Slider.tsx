// eslint-disable-next-line no-restricted-imports
import {
  MultiSlider as BlueprintMultiSlider,
  MultiSliderProps as BlueprintMultiSliderProps,
  Slider as BlueprintSlider,
  SliderProps as BlueprintSliderProps,
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
  .bp5-slider-track {
    height: 8px;
    .bp5-slider-progress {
      background-color: ${(p) => p.$fillColor};
      opacity: 0.4;
      height: 8px;
    }
    .bp5-slider-progress.bp5-intent-primary {
      background-color: ${(p) => p.$fillColor};
      opacity: 1;
      height: 8px;
    }
  }
  &.bp5-vertical {
    width: 20px;
    min-width: 20px;
  }
  &.bp5-vertical .bp5-slider-track,
  &.bp5-vertical .bp5-slider-track .bp5-slider-progress {
    height: initial;
    width: 8px;
  }
  .bp5-slider-handle {
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

    .bp5-slider-label {
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
