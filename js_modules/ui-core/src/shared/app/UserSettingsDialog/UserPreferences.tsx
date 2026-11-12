import {
  Box,
  Button,
  Checkbox,
  Colors,
  DagsterTheme,
  FontFamily,
  Heading,
  Icon,
  Slider,
  Tooltip,
} from '@dagster-io/ui-components';
import React, {useContext} from 'react';

import {SHORTCUTS_STORAGE_KEY} from '../../../app/ShortcutHandler';
import {useShowAssetsWithoutDefinitions} from '../../../app/UserSettingsDialog/useShowAssetsWithoutDefinitions';
import {HourCycleSelect} from '../../../app/time/HourCycleSelect';
import {ThemeSelect} from '../../../app/time/ThemeSelect';
import {TimeContext} from '../../../app/time/TimeContext';
import {TimezoneSelect} from '../../../app/time/TimezoneSelect';
import {localTimezoneLabel, orgTimezoneLabel} from '../../../app/time/browserTimezone';
import {requestRefreshEverywhere} from '../../../app/useReloadOnNewBuild';
import {useThemeState} from '../../../app/useThemeState';
import {useFallLeavesEnabled} from '../../../hillpointe/FallLeaves';
import {ROTATE_MAX_SECS, useTimingsRotateSecs} from '../../../hillpointe/timingsRotation';
import {useStateWithStorage} from '../../../hooks/useStateWithStorage';

export const UserPreferences = ({
  onChangeRequiresReload,
  orgTimezone,
}: {
  onChangeRequiresReload: (requiresReload: boolean) => void;
  orgTimezone?: string | null;
}) => {
  const [shortcutsEnabled, setShortcutsEnabled] = useStateWithStorage(
    SHORTCUTS_STORAGE_KEY,
    (value: any) => (typeof value === 'boolean' ? value : true),
  );
  const {theme, setTheme} = useThemeState();
  const [fallLeavesEnabled, setFallLeavesEnabled] = useFallLeavesEnabled();
  const [rotateSecs, setRotateSecs] = useTimingsRotateSecs();

  const initialShortcutsEnabled = React.useRef(shortcutsEnabled);

  const lastChangeValue = React.useRef(false);
  React.useEffect(() => {
    const didChange = initialShortcutsEnabled.current !== shortcutsEnabled;
    if (lastChangeValue.current !== didChange) {
      onChangeRequiresReload(didChange);
      lastChangeValue.current = didChange;
    }
  }, [shortcutsEnabled, theme, onChangeRequiresReload]);

  const {
    timezone: [timezone, setTimezone],
  } = useContext(TimeContext);

  const triggerLabel = React.useMemo(() => {
    if (timezone === 'ORG_TIMEZONE' && orgTimezone) {
      return orgTimezoneLabel(orgTimezone);
    }

    if (timezone === 'LOCAL_TIMEZONE' || timezone === 'Automatic') {
      return localTimezoneLabel();
    }

    return timezone;
  }, [timezone, orgTimezone]);

  const trigger = React.useCallback(
    (_timezone: string) => (
      <Button
        rightIcon={<Icon name="arrow_drop_down" />}
        style={{minWidth: '200px', display: 'flex', justifyContent: 'space-between'}}
      >
        {triggerLabel}
      </Button>
    ),
    [triggerLabel],
  );

  const toggleKeyboardShortcuts = (e: React.ChangeEvent<HTMLInputElement>) => {
    const {checked} = e.target;
    setShortcutsEnabled(checked);
  };

  return (
    <>
      <Box padding={{bottom: 4}}>
        <Heading size={14} weight={600}>
          Preferences
        </Heading>
      </Box>
      <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <div>Timezone</div>
        <TimezoneSelect
          timezone={timezone}
          setTimezone={setTimezone}
          orgTimezone={orgTimezone}
          trigger={trigger}
          popoverProps={{position: 'bottom-right'}}
        />
      </Box>
      <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <div>Hour format</div>
        <HourCycleSelect />
      </Box>
      <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <div>Theme</div>
        <ThemeSelect theme={theme} onChange={setTheme} />
      </Box>
      {theme === DagsterTheme.Fall ? (
        <Box padding={{vertical: 8}} flex={{justifyContent: 'space-between', alignItems: 'center'}}>
          <div>Falling leaves</div>
          <Checkbox
            checked={fallLeavesEnabled}
            format="switch"
            onChange={(e) => setFallLeavesEnabled(e.target.checked)}
          />
        </Box>
      ) : null}
      <Box padding={{vertical: 8}} flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <div>Enable keyboard shortcuts</div>
        <Checkbox checked={shortcutsEnabled} format="switch" onChange={toggleKeyboardShortcuts} />
      </Box>
      <Box padding={{vertical: 8}} flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
          <div>Job timings rotation</div>
          <Tooltip content="How long Job timings shows each live job before moving to the next. Drag to zero to turn it off. Saved on this device only.">
            <Icon name="info" />
          </Tooltip>
        </Box>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
          <div style={{width: 160}}>
            <Slider
              value={rotateSecs}
              onChange={setRotateSecs}
              min={0}
              max={ROTATE_MAX_SECS}
              step={5}
            />
          </div>
          <div style={{minWidth: 72, textAlign: 'right'}}>
            {rotateSecs ? `Every ${rotateSecs}s` : 'Off'}
          </div>
        </Box>
      </Box>
    </>
  );
};

/** Settings only someone maintaining the site needs; the dialog keeps them folded away. */
export const DeveloperPreferences = () => {
  const {showAssetsWithoutDefinitions, setShowAssetsWithoutDefinitions} =
    useShowAssetsWithoutDefinitions();
  return (
    <>
      <Box padding={{vertical: 8}} flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
          <div>Show assets without definitions in catalog</div>
          <Tooltip content="Hide assets that lack current code definitions (typically legacy or orphaned assets with only historical materialization data) to focus on actively managed assets">
            <Icon name="info" />
          </Tooltip>
        </Box>
        <Checkbox
          checked={showAssetsWithoutDefinitions}
          format="switch"
          onChange={(e) => setShowAssetsWithoutDefinitions(e.target.checked)}
        />
      </Box>
      <Box padding={{vertical: 8}} flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <div>Build</div>
        <BuildInfo />
      </Box>
      <Box padding={{vertical: 8}} flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
          <div>Refresh every screen</div>
          <Tooltip content="Reloads this site on every device that has it open, such as the TV, within about 30 seconds.">
            <Icon name="info" />
          </Tooltip>
        </Box>
        <RefreshEverywhereButton />
      </Box>
    </>
  );
};

const RefreshEverywhereButton = () => {
  const [state, setState] = React.useState<'idle' | 'sending' | 'sent' | 'failed'>('idle');
  const send = async () => {
    setState('sending');
    setState((await requestRefreshEverywhere()) ? 'sent' : 'failed');
  };
  return (
    <Button icon={<Icon name="refresh" />} onClick={send} disabled={state === 'sending'}>
      {state === 'sent' ? 'Sent' : state === 'failed' ? 'Failed, try again' : 'Refresh now'}
    </Button>
  );
};

// Set by the wheel-building workflow; absent in local development.
const BUILD_COMMIT = process.env.NEXT_PUBLIC_BUILD_COMMIT;
const BUILD_REPO = process.env.NEXT_PUBLIC_BUILD_REPO;
const BUILD_TIME = process.env.NEXT_PUBLIC_BUILD_TIME;

/** Which commit this UI was built from, so a running site can be matched to the code. */
export const BuildInfo = () => {
  if (!BUILD_COMMIT) {
    return <span style={{color: Colors.textLight()}}>Local development build</span>;
  }
  const short = BUILD_COMMIT.slice(0, 7);
  const built = BUILD_TIME ? new Date(BUILD_TIME).toLocaleString() : null;
  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
      {BUILD_REPO ? (
        <a
          href={`https://github.com/${BUILD_REPO}/commit/${BUILD_COMMIT}`}
          target="_blank"
          rel="noreferrer"
          style={{fontFamily: FontFamily.monospace}}
        >
          {short}
        </a>
      ) : (
        <span style={{fontFamily: FontFamily.monospace}}>{short}</span>
      )}
      {built ? <span style={{color: Colors.textLight()}}>built {built}</span> : null}
    </Box>
  );
};
