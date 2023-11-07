import {MenuDivider, MenuItem, Menu, Select} from '@dagster-io/ui-components';
import * as React from 'react';

import {TimeContext} from './TimeContext';
import {browserTimezone, browserTimezoneAbbreviation} from './browserTimezone';

/**
 * Render the target date as a string in en-US with the timezone supplied, and use
 * that to extract the GMT offset (+/- HH:MM) of the provided timezone.
 *
 * We use `toLocaleDateString` instead of `formatToParts` here so that we don't have
 * to create new Intl.DateTimeFormat objects for every timezone we're looking at.
 */
const extractOffset = (targetDate: Date, timeZone: string) => {
  const formatted = targetDate.toLocaleDateString('en-US', {
    year: 'numeric',
    timeZone,
    timeZoneName: 'longOffset',
  });
  const [_, gmtOffset] = formatted.split(', ');
  const stripped = gmtOffset!.replace(/^GMT/, '').replace(/:/, '');

  // Already GMT.
  if (stripped === '') {
    return {label: '0:00', value: 0};
  }

  const plusMinus = stripped[0];
  const hours = stripped.slice(1, 3).replace(/^0/, '');
  const minutes = stripped.slice(3);

  const hourValue = parseInt(`${plusMinus}${hours}`, 10);
  const minValue = parseInt(`${plusMinus}${minutes}`, 10) / 60;

  return {label: `${plusMinus}${hours}:${minutes}`, value: hourValue + minValue};
};

const POPULAR_TIMEZONES = new Set([
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
]);

interface Props {
  trigger: (timezone: string) => React.ReactNode;
}

/**
 * Show a list of timezones that the user can choose from. The selected timezone
 * is tracked in localStorage. Show sections of timezones, in this order:
 *
 * - Automatic timezone: whatever the user's browser/locale thinks they're in.
 * - Popular timezones: the four US timezones.
 * - Locale timezones: other timezones for the user's locale, if possible.
 * - Everything else
 */
export const TimezoneSelect = ({trigger}: Props) => {
  const {
    timezone: [timezone, setTimezone],
  } = React.useContext(TimeContext);

  const allTimezoneItems = React.useMemo(() => {
    const date = new Date();

    let allTimezoneItems: {offsetLabel: string; offset: number; key: string}[] = [];
    let explicitlyAddUTC = true;
    try {
      allTimezoneItems = Intl.supportedValuesOf('timeZone')
        .map((timeZone) => {
          const {label, value} = extractOffset(date, timeZone);
          return {offsetLabel: label, offset: value, key: timeZone};
        })
        .sort((a, b) => a.offset - b.offset);
      // Some browsers include UTC. (Firefox) Some don't. (Chrome, Safari)
      // Determine whether we need to explicitly add it to the list.
      explicitlyAddUTC = !allTimezoneItems.some((tz) => tz.key === 'UTC');
    } catch (e) {
      // `Intl.supportedValuesOf` is unavailable in this browser. Only
      // support the Automatic timezone and UTC.
    }

    const automaticOffsetLabel = () => {
      const abbreviation = browserTimezoneAbbreviation();
      const {label} = extractOffset(date, browserTimezone());
      return `${abbreviation} ${label}`;
    };

    const locale = new Intl.Locale(navigator.language);
    const timezonesForLocaleSet = new Set<string>(
      'timeZones' in locale ? (locale.timeZones as string[]) : [],
    );

    const timezonesForLocale = allTimezoneItems.filter(
      (tz) => timezonesForLocaleSet.has(tz.key) && !POPULAR_TIMEZONES.has(tz.key),
    );

    return [
      {
        key: 'Automatic',
        offsetLabel: automaticOffsetLabel(),
        offset: 0,
      },
      {
        key: 'divider-1',
        offsetLabel: '',
        offset: 0,
      },
      ...(explicitlyAddUTC
        ? [
            {
              key: 'UTC',
              offsetLabel: '0:00',
              offset: 0,
            },
          ]
        : []),
      ...allTimezoneItems.filter((tz) => POPULAR_TIMEZONES.has(tz.key)),
      ...(timezonesForLocale.length
        ? [
            {
              key: 'divider-2',
              offsetLabel: '',
              offset: 0,
            },
            ...timezonesForLocale,
          ]
        : []),
      {
        key: 'divider-3',
        offsetLabel: '',
        offset: 0,
      },
      ...allTimezoneItems.filter(
        (tz) => !POPULAR_TIMEZONES.has(tz.key) && !timezonesForLocaleSet.has(tz.key),
      ),
    ];
  }, []);

  return (
    <Select<(typeof allTimezoneItems)[0]>
      popoverProps={{
        position: 'bottom-left',
        modifiers: {offset: {enabled: true, offset: '-12px, 8px'}},
      }}
      activeItem={allTimezoneItems.find((tz) => tz.key === timezone)}
      inputProps={{style: {width: '300px'}}}
      items={allTimezoneItems}
      itemPredicate={(query, tz) => tz.key.toLowerCase().includes(query.toLowerCase())}
      itemRenderer={(tz, props) =>
        tz.key.startsWith('divider') ? (
          <MenuDivider key={tz.key} />
        ) : (
          <MenuItem
            active={props.modifiers.active}
            onClick={props.handleClick}
            label={tz.offsetLabel}
            key={tz.key}
            text={tz.key}
          />
        )
      }
      itemListRenderer={({renderItem, filteredItems}) => {
        const renderedItems = filteredItems.map(renderItem).filter(Boolean);
        return <Menu>{renderedItems}</Menu>;
      }}
      noResults={<MenuItem disabled text="No results." />}
      onItemSelect={(tz) => setTimezone(tz.key)}
    >
      {trigger(timezone)}
    </Select>
  );
};
