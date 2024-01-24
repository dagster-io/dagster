import {Colors} from '@dagster-io/ui-components';
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
    background-color: ${Colors.backgroundDefault()};
  }

  .DateRangePickerInput__withBorder {
    border-color: ${Colors.borderDefault()};
  }

  .DateInput {
    background-color: ${Colors.backgroundDefault()};
  }

  .DateRangePickerInput_arrow_svg {
    fill: ${Colors.textLighter()};
  }

  .DateInput_input {
    background-color: ${Colors.backgroundDefault()};
    color: ${Colors.textDefault()};
  }

  .DateInput_input::placeholder {
    color: ${Colors.textLight()};
  }

  .DateInput_input__focused {
    border-color: ${Colors.accentBlue()};
    outline: none;
  }

  .DateInput_fangShape {
    fill: ${Colors.backgroundLight()};
  }

  .DateInput_fangStroke {
    stroke: ${Colors.keylineDefault()};
  }

  .DateRangePicker_picker {
    background-color: ${Colors.backgroundLight()};
    color: ${Colors.textDefault()};
  }

  .DayPicker {
    background-color: ${Colors.backgroundLight()};
    color: ${Colors.textDefault()};
  }

  .DayPickerNavigation_button__default {
    background-color: ${Colors.backgroundLight()};
    border-color: ${Colors.borderDefault()};

    :hover {
      border-color: ${Colors.borderHover()};
    }
  }

  .DayPickerNavigation_svg__horizontal {
    fill: ${Colors.textLight()};
  }

  .DayPicker_weekHeader {
    color: ${Colors.textLighter()};
  }

  .CalendarMonthGrid,
  .CalendarMonth {
    background-color: ${Colors.backgroundLight()};
    color: ${Colors.textDefault()};
  }

  .CalendarMonth_caption {
    color: ${Colors.textLight()};
  }

  .CalendarDay__default {
    background-color: ${Colors.backgroundLight()};
    border-color: ${Colors.keylineDefault()};
    color: ${Colors.textLight()};

    :hover {
      background-color: ${Colors.backgroundBlue()};
      border-color: ${Colors.keylineDefault()};
    }
  }

  .CalendarDay__selected {
    background-color: ${Colors.backgroundBlueHover()};

    :active,
    :hover {
      border-color: ${Colors.keylineDefault()};
    }
  }

  .CalendarDay__hovered_span,
  .CalendarDay__hovered_span_3 {
    background-color: ${Colors.backgroundBlue()};
    border-color: ${Colors.keylineDefault()};
  }
`;

// eslint-disable-next-line import/no-default-export
export default DateRangePickerWrapper;
