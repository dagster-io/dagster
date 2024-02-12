import {Button, Icon, Menu, MenuItem, Select} from '@dagster-io/ui-components';
import {useContext, useEffect, useMemo, useState} from 'react';

import {HourCycle} from './HourCycle';
import {TimeContext} from './TimeContext';
import {browserHourCycle} from './browserTimezone';

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
export const HourCycleSelect = () => {
  const {
    hourCycle: [hourCycle, setHourCycle],
  } = useContext(TimeContext);

  const [date, setDate] = useState(() => new Date());

  const formats = useMemo(() => {
    return {
      automatic: new Intl.DateTimeFormat(navigator.language, {timeStyle: 'short'}),
      h12: new Intl.DateTimeFormat(navigator.language, {hourCycle: 'h12', timeStyle: 'short'}),
      h23: new Intl.DateTimeFormat(navigator.language, {hourCycle: 'h23', timeStyle: 'short'}),
    };
  }, []);

  const labels = useMemo(() => {
    return {
      automatic: `Automatic (${browserHourCycle() === 'h12' ? '12-hour' : '24-hour'})`,
      h12: '12-hour',
      h23: '24-hour',
    };
  }, []);

  useEffect(() => {
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
    <Select<(typeof items)[0]>
      popoverProps={{
        position: 'bottom-right',
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
      <Button
        rightIcon={<Icon name="arrow_drop_down" />}
        style={{minWidth: '200px', display: 'flex', justifyContent: 'space-between'}}
      >
        {hourCycle === 'Automatic' || !hourCycle ? labels.automatic : labels[hourCycle]}
      </Button>
    </Select>
  );
};
