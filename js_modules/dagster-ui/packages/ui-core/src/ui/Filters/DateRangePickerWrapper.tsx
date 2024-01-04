import * as React from 'react';
import {DateRangePicker} from 'react-dates';

import 'react-dates/initialize';
import 'react-dates/lib/css/_datepicker.css';

export const DateRangePickerWrapper = (props: React.ComponentProps<typeof DateRangePicker>) => {
  return <DateRangePicker {...props} />;
};

// eslint-disable-next-line import/no-default-export
export default DateRangePicker;
