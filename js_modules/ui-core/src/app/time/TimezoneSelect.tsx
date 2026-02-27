import {Box, Menu, MenuDivider, MenuItem, Select} from '@dagster-io/ui-components';
import {ComponentProps, useMemo} from 'react';

import {
  browserTimezone,
  browserTimezoneAbbreviation,
  timezoneAbbreviation,
} from './browserTimezone';

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
  const stripped = (gmtOffset ?? '').replace(/^GMT/, '').replace(/:/, '');

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

interface TimezoneSelectProps {
  timezone: string;
  setTimezone: (timezone: string) => void;
  trigger: (timezone: string) => React.ReactNode;
  orgTimezone?: string | null;
  /**
   * When `true`, only show IANA timezone values — hide the "Org timezone"
   * and "Local timezone" options. Use this when the user must choose a
   * specific timezone. Defaults to `false`.
   */
  ianaOnly?: boolean;
  popoverProps?: ComponentProps<typeof Select>['popoverProps'];
}

/**
 * Show a list of timezones that the user can choose from. The selected timezone
 * is tracked in localStorage. Show sections of timezones, in this order:
 *
 * - Organization timezone: the org's default timezone (if configured).
 * - Local timezone: whatever the user's browser/locale thinks they're in.
 * - UTC and popular US timezones.
 * - Locale timezones: other timezones for the user's locale, if possible.
 * - Everything else
 */
export const TimezoneSelect = ({
  timezone,
  setTimezone,
  trigger,
  orgTimezone,
  ianaOnly = false,
  popoverProps,
}: TimezoneSelectProps) => {
  const allTimezoneItems = useMemo(() => {
    const date = new Date();

    let allTimezoneItems: {offsetLabel: string; offset: number; key: string; text?: string}[] = [];
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
    } catch {
      // `Intl.supportedValuesOf` is unavailable in this browser. Only
      // support the Local timezone and UTC.
    }

    const localOffsetLabel = () => {
      const abbreviation = browserTimezoneAbbreviation();
      const {label} = extractOffset(date, browserTimezone());
      return `${abbreviation} ${label}`;
    };

    const orgOffsetLabel = (tz: string) => {
      const abbreviation = timezoneAbbreviation(tz);
      const {label} = extractOffset(date, tz);
      return `${abbreviation} ${label}`;
    };

    const locale = new Intl.Locale(navigator.language);
    const timezonesForLocaleSet = new Set<string>(
      'timeZones' in locale ? (locale.timeZones as string[]) : [],
    );

    const timezonesForLocale = allTimezoneItems.filter(
      (tz) => timezonesForLocaleSet.has(tz.key) && !POPULAR_TIMEZONES.has(tz.key),
    );

    const shortcutItems = !ianaOnly
      ? [
          ...(orgTimezone
            ? [
                {
                  key: 'ORG_TIMEZONE',
                  text: 'Org timezone',
                  offsetLabel: orgOffsetLabel(orgTimezone),
                  offset: 0,
                },
              ]
            : []),
          {
            key: 'LOCAL_TIMEZONE',
            text: 'Local timezone',
            offsetLabel: localOffsetLabel(),
            offset: 0,
          },
          {
            key: 'divider-1',
            offsetLabel: '',
            offset: 0,
          },
        ]
      : [];

    return [
      ...shortcutItems,
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
  }, [orgTimezone, ianaOnly]);

  return (
    <Select<(typeof allTimezoneItems)[0]>
      popoverProps={
        popoverProps ?? {
          position: 'bottom-left',
        }
      }
      activeItem={allTimezoneItems.find((tz) => tz.key === timezone)}
      inputProps={{style: {width: '300px'}}}
      items={allTimezoneItems}
      itemPredicate={(query, tz) => (tz.text ?? tz.key).toLowerCase().includes(query.toLowerCase())}
      itemRenderer={(tz, props) =>
        tz.key.startsWith('divider') ? (
          <MenuDivider key={tz.key} />
        ) : (
          <MenuItem
            active={props.modifiers.active}
            onClick={props.handleClick}
            right={tz.offsetLabel}
            key={tz.key}
            text={tz.text ?? tz.key}
          />
        )
      }
      itemListRenderer={({renderItem, filteredItems}) => {
        const renderedItems = filteredItems.map(renderItem).filter(Boolean);
        return (
          <Menu style={{maxHeight: '300px', overflowY: 'auto'}}>
            <Box padding={{vertical: 4}}>{renderedItems}</Box>
          </Menu>
        );
      }}
      noResults={<MenuItem disabled text="No results." />}
      onItemSelect={(tz) => setTimezone(tz.key)}
    >
      {trigger(timezone)}
    </Select>
  );
};
