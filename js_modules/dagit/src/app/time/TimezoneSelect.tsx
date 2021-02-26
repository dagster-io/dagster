import {Menu} from '@blueprintjs/core';
import {Select} from '@blueprintjs/select';
import moment from 'moment-timezone';
import * as React from 'react';

import {TimezoneContext} from 'src/app/time/TimezoneContext';
import {browserTimezone, browserTimezoneAbbreviation} from 'src/app/time/browserTimezone';

const formatOffset = (mm: number) => {
  const amm = Math.abs(mm);
  // moment.tz.zone() offsets are inverted: https://momentjs.com/timezone/docs/#/zone-object/offset/
  return `${mm < 0 ? '+' : '-'}${Math.floor(amm / 60)}:${amm % 60 < 10 ? '0' : ''}${amm % 60}`;
};

const AllTimezoneItems = moment.tz
  .names()
  .map((key) => {
    const offset = moment.tz.zone(key)?.utcOffset(Date.now()) || 0;
    return {offsetLabel: `${formatOffset(offset)}`, offset, key};
  })
  .sort((a, b) => a.offset - b.offset);

const PopularTimezones = ['UTC', 'US/Pacific', 'US/Mountain', 'US/Central', 'US/Eastern'];

const offsetLabel = () => {
  return `${browserTimezoneAbbreviation()} ${formatOffset(
    moment.tz.zone(browserTimezone())?.utcOffset(Date.now()) || 0,
  )}`;
};

const SortedTimezoneItems = [
  {
    key: 'Automatic',
    offsetLabel: offsetLabel(),
    offset: 0,
  },
  {
    key: 'divider-1',
    offsetLabel: '',
    offset: 0,
  },
  ...AllTimezoneItems.filter((t) => PopularTimezones.includes(t.key)),
  {
    key: 'divider-2',
    offsetLabel: '',
    offset: 0,
  },
  ...AllTimezoneItems.filter((t) => !PopularTimezones.includes(t.key)),
];

interface Props {
  trigger: (timezone: string) => React.ReactNode;
}

export const TimezoneSelect: React.FC<Props> = ({trigger}) => {
  const [timezone, setTimezone] = React.useContext(TimezoneContext);

  return (
    <Select<typeof SortedTimezoneItems[0]>
      popoverProps={{position: 'bottom-right'}}
      activeItem={SortedTimezoneItems.find((tz) => tz.key === timezone)}
      inputProps={{style: {width: '300px'}}}
      items={SortedTimezoneItems}
      itemPredicate={(query, tz) => tz.key.toLowerCase().includes(query.toLowerCase())}
      itemRenderer={(tz, props) =>
        tz.key.startsWith('divider') ? (
          <Menu.Divider key={tz.key} />
        ) : (
          <Menu.Item
            active={props.modifiers.active}
            onClick={props.handleClick}
            label={tz.offsetLabel}
            key={tz.key}
            text={tz.key}
          />
        )
      }
      noResults={<Menu.Item disabled text="No results." />}
      onItemSelect={(tz) => setTimezone(tz.key)}
    >
      {trigger(timezone)}
    </Select>
  );
};
