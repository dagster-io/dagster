import {DateRange, DayPicker, DayPickerProps} from 'react-day-picker';
import 'react-day-picker/style.css';

import styles from './css/DayPickerWrapper.module.css';

export type {DateRange};

export const DayPickerWrapper = (props: DayPickerProps) => {
  return (
    <div className={styles.dayPickerWrapper}>
      <DayPicker {...props} />
    </div>
  );
};
