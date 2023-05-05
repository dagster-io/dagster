import {MenuItem, Menu, Select, ButtonLink} from '@dagster-io/ui';
import * as React from 'react';

import {HourCycle} from './HourCycle';
import {TimeContext} from './TimeContext';

/**
 * Show the "hour cycle" options available to the user:
 *
 * - 12-hour cycle, which displays AM/PM
 * - 23-hour cycle, e.g. military time, which shows midnight as 00 and does not use AM/PM
 *   - We'll call this one "24-hour" because that's a more familiar name for it
 *
 * We detect the automatic behavior for the user's locale and show that as an option
 * as well. The user can override this with one of the choices above.
 */
export const HourCycleSelect: React.FC = () => {
  const {
    hourCycle: [hourCycle, setHourCycle],
  } = React.useContext(TimeContext);

  const [date, setDate] = React.useState(() => new Date());

  const formats = React.useMemo(() => {
    return {
      automatic: new Intl.DateTimeFormat(navigator.language, {timeStyle: 'short'}),
      h12: new Intl.DateTimeFormat(navigator.language, {hourCycle: 'h12', timeStyle: 'short'}),
      h23: new Intl.DateTimeFormat(navigator.language, {hourCycle: 'h23', timeStyle: 'short'}),
    };
  }, []);

  const labels = React.useMemo(() => {
    // Detect the hour cycle based on the presence of a dayPeriod in a formatted time string,
    // since the `hourCycle` property on the Intl.Locale object may be undefined.
    const parts = formats.automatic.formatToParts(new Date());
    const partKeys = parts.map((part) => part.type);
    return {
      automatic: `Automatic (${partKeys.includes('dayPeriod') ? '12-hour' : '24-hour'})`,
      h12: '12-hour',
      h23: '24-hour',
    };
  }, [formats.automatic]);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setDate(new Date());
    }, 1000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  const items = [
    {
      key: 'Automatic',
      text: labels.automatic,
      label: formats.automatic.format(date),
      offset: 0,
    },
    {
      key: 'h12',
      text: labels.h12,
      label: formats.h12.format(date),
      offset: 0,
    },
    {
      key: 'h23',
      text: labels.h23,
      label: formats.h23.format(date),
      offset: 0,
    },
  ];

  return (
    <Select<typeof items[0]>
      popoverProps={{
        position: 'bottom-left',
        modifiers: {offset: {enabled: true, offset: '-12px, 8px'}},
      }}
      filterable={false}
      activeItem={items.find((item) => item.key === hourCycle)}
      items={items}
      itemRenderer={(item, props) => {
        return (
          <MenuItem
            active={props.modifiers.active}
            onClick={props.handleClick}
            label={item.label}
            key={item.key}
            text={item.text}
            style={{width: '300px'}}
          />
        );
      }}
      itemListRenderer={({renderItem, filteredItems}) => {
        const renderedItems = filteredItems.map(renderItem).filter(Boolean);
        return <Menu>{renderedItems}</Menu>;
      }}
      onItemSelect={(item) => setHourCycle(item.key as HourCycle)}
    >
      <ButtonLink>
        {hourCycle === 'Automatic' || !hourCycle ? labels.automatic : labels[hourCycle]}
      </ButtonLink>
    </Select>
  );
};
