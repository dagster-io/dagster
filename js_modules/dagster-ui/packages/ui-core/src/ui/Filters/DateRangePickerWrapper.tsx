import {
  colorAccentBlue,
  colorBackgroundBlue,
  colorBackgroundBlueHover,
  colorBackgroundDefault,
  colorBackgroundLight,
  colorBorderDefault,
  colorBorderHover,
  colorKeylineDefault,
  colorTextDefault,
  colorTextLight,
  colorTextLighter,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {DateRangePicker} from 'react-dates';
import styled from 'styled-components';

import 'react-dates/initialize';
import 'react-dates/lib/css/_datepicker.css';

export const DateRangePickerWrapper = (props: React.ComponentProps<typeof DateRangePicker>) => {
  return (
    <DatePickerContainer>
      <DateRangePicker {...props} />
    </DatePickerContainer>
  );
};

const DatePickerContainer = styled.div`
  .DateRangePickerInput {
    background-color: ${colorBackgroundDefault()};
  }

  .DateRangePickerInput__withBorder {
    border-color: ${colorBorderDefault()};
  }

  .DateInput {
    background-color: ${colorBackgroundDefault()};
  }

  .DateRangePickerInput_arrow_svg {
    fill: ${colorTextLighter()};
  }

  .DateInput_input {
    background-color: ${colorBackgroundDefault()};
    color: ${colorTextDefault()};
  }

  .DateInput_input::placeholder {
    color: ${colorTextLight()};
  }

  .DateInput_input__focused {
    border-color: ${colorAccentBlue()};
    outline: none;
  }

  .DateInput_fangShape {
    fill: ${colorBackgroundLight()};
  }

  .DateInput_fangStroke {
    stroke: ${colorKeylineDefault()};
  }

  .DateRangePicker_picker {
    background-color: ${colorBackgroundLight()};
    color: ${colorTextDefault()};
  }

  .DayPicker {
    background-color: ${colorBackgroundLight()};
    color: ${colorTextDefault()};
  }

  .DayPickerNavigation_button__default {
    background-color: ${colorBackgroundLight()};
    border-color: ${colorBorderDefault()};

    :hover {
      border-color: ${colorBorderHover()};
    }
  }

  .DayPickerNavigation_svg__horizontal {
    fill: ${colorTextLight()};
  }

  .DayPicker_weekHeader {
    color: ${colorTextLighter()};
  }

  .CalendarMonthGrid,
  .CalendarMonth {
    background-color: ${colorBackgroundLight()};
    color: ${colorTextDefault()};
  }

  .CalendarMonth_caption {
    color: ${colorTextLight()};
  }

  .CalendarDay__default {
    background-color: ${colorBackgroundLight()};
    border-color: ${colorKeylineDefault()};
    color: ${colorTextLight()};

    :hover {
      background-color: ${colorBackgroundBlue()};
      border-color: ${colorKeylineDefault()};
    }
  }

  .CalendarDay__selected {
    background-color: ${colorBackgroundBlueHover()};

    :active,
    :hover {
      border-color: ${colorKeylineDefault()};
    }
  }

  .CalendarDay__hovered_span,
  .CalendarDay__hovered_span_3 {
    background-color: ${colorBackgroundBlue()};
    border-color: ${colorKeylineDefault()};
  }
`;

// eslint-disable-next-line import/no-default-export
export default DateRangePickerWrapper;
