import {render, screen} from '@testing-library/react';

import {TimeContext, type TimeContextValue} from '../../app/time/TimeContext';
import {TimeDividers} from '../RunTimeline';
import styles from '../css/RunTimeline.module.css';

const ONE_MINUTE = 60 * 1000;
const RANGE_START = Date.UTC(2026, 7, 22, 8);
const RANGE_END = RANGE_START + 4 * 60 * ONE_MINUTE;
const TEN_MINUTES = 10 * ONE_MINUTE;

const timeContextValue = (hourCycle: 'h12' | 'h23') =>
  ({
    timezone: ['UTC', () => 'UTC', () => {}],
    resolvedTimezone: 'UTC',
    hourCycle: [hourCycle, () => hourCycle, () => {}],
  }) as TimeContextValue;

const elementsForClass = (container: HTMLElement, className: string | undefined) => {
  if (!className) {
    throw new Error('Expected CSS module class name');
  }
  return container.getElementsByClassName(className);
};

const TestTimeline = ({hourCycle = 'h12', width}: {hourCycle?: 'h12' | 'h23'; width: number}) => (
  <TimeContext.Provider value={timeContextValue(hourCycle)}>
    <TimeDividers
      annotations={[
        {label: 'Start', ms: RANGE_START + 20 * ONE_MINUTE},
        {label: 'End', ms: RANGE_END - 20 * ONE_MINUTE},
      ]}
      height={160}
      interval={TEN_MINUTES}
      now={RANGE_START + 150 * ONE_MINUTE}
      rangeMs={[RANGE_START, RANGE_END]}
      width={width}
    />
  </TimeContext.Provider>
);

describe('TimeDividers', () => {
  it('changes label density without removing dividers or independent markers', () => {
    const {container, rerender} = render(<TestTimeline width={240} />);

    const narrowLabelCount = elementsForClass(container, styles.timeLabel).length;
    const narrowDividerCount = elementsForClass(container, styles.dividerLine).length;

    expect(narrowLabelCount).toBe(1);
    expect(screen.getByText('Now')).toBeVisible();
    expect(screen.getByText('Start')).toBeVisible();
    expect(screen.getByText('End')).toBeVisible();

    rerender(<TestTimeline width={720} />);

    expect(elementsForClass(container, styles.timeLabel)).toHaveLength(5);
    expect(elementsForClass(container, styles.dividerLine)).toHaveLength(narrowDividerCount);
    expect(elementsForClass(container, styles.timeLabel).length).toBeGreaterThan(narrowLabelCount);
    expect(screen.getByText('Now')).toBeVisible();
    expect(screen.getByText('Start')).toBeVisible();
    expect(screen.getByText('End')).toBeVisible();
  });

  it('uses denser spacing for shorter 24-hour labels', () => {
    const {container, rerender} = render(<TestTimeline hourCycle="h12" width={240} />);

    expect(elementsForClass(container, styles.timeLabel)).toHaveLength(1);

    rerender(<TestTimeline hourCycle="h23" width={240} />);

    expect(elementsForClass(container, styles.timeLabel)).toHaveLength(3);
  });
});
