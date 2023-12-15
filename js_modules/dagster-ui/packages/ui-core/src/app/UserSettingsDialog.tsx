import {
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogBody,
  DialogFooter,
  MetadataTable,
  Subheading,
  Icon,
} from '@dagster-io/ui-components';
import {DAGSTER_THEME_KEY, DagsterTheme} from '@dagster-io/ui-components/src/theme/theme';
import * as React from 'react';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

import {FeatureFlagType, getFeatureFlags, setFeatureFlags} from './Flags';
import {SHORTCUTS_STORAGE_KEY} from './ShortcutHandler';
import {HourCycleSelect} from './time/HourCycleSelect';
import {ThemeSelect} from './time/ThemeSelect';
import {TimezoneSelect} from './time/TimezoneSelect';
import {automaticLabel} from './time/browserTimezone';

type OnCloseFn = (event: React.SyntheticEvent<HTMLElement>) => void;
type VisibleFlag = {key: string; label?: React.ReactNode; flagType: FeatureFlagType};

interface DialogProps {
  isOpen: boolean;
  onClose: OnCloseFn;
  visibleFlags: VisibleFlag[];
}

export const UserSettingsDialog = ({isOpen, onClose, visibleFlags}: DialogProps) => {
  return (
    <Dialog
      title="User settings"
      isOpen={isOpen}
      canOutsideClickClose={false}
      canEscapeKeyClose={false}
    >
      <UserSettingsDialogContent onClose={onClose} visibleFlags={visibleFlags} />
    </Dialog>
  );
};

interface DialogContentProps {
  onClose: OnCloseFn;
  visibleFlags: {key: string; label?: React.ReactNode; flagType: FeatureFlagType}[];
}

/**
 * Separate the content from the `Dialog` so that we don't prepare its state before
 * we want to render it.
 */
const UserSettingsDialogContent = ({onClose, visibleFlags}: DialogContentProps) => {
  const [flags, setFlags] = React.useState<FeatureFlagType[]>(() => getFeatureFlags());
  const [reloading, setReloading] = React.useState(false);

  const [shortcutsEnabled, setShortcutsEnabled] = useStateWithStorage(
    SHORTCUTS_STORAGE_KEY,
    (value: any) => (typeof value === 'boolean' ? value : true),
  );

  const [theme, setTheme] = useStateWithStorage(DAGSTER_THEME_KEY, (value: any) => {
    if (
      value === DagsterTheme.Light ||
      value === DagsterTheme.Dark ||
      value === DagsterTheme.System ||
      value === DagsterTheme.Legacy
    ) {
      return value;
    }
    return DagsterTheme.Legacy;
  });

  const initialFlagState = React.useRef(JSON.stringify([...getFeatureFlags().sort()]));
  const initialShortcutsEnabled = React.useRef(shortcutsEnabled);
  const initialTheme = React.useRef(theme);

  React.useEffect(() => {
    setFeatureFlags(flags);
  });

  const toggleFlag = (flag: FeatureFlagType) => {
    setFlags(flags.includes(flag) ? flags.filter((f) => f !== flag) : [...flags, flag]);
  };

  const trigger = React.useCallback(
    (timezone: string) => (
      <Button
        rightIcon={<Icon name="arrow_drop_down" />}
        style={{minWidth: '200px', display: 'flex', justifyContent: 'space-between'}}
      >
        {timezone === 'Automatic' ? automaticLabel() : timezone}
      </Button>
    ),
    [],
  );

  const toggleKeyboardShortcuts = (e: React.ChangeEvent<HTMLInputElement>) => {
    const {checked} = e.target;
    setShortcutsEnabled(checked);
  };

  const anyChange =
    initialFlagState.current !== JSON.stringify([...flags.sort()]) ||
    initialShortcutsEnabled.current !== shortcutsEnabled ||
    initialTheme.current !== theme;

  const handleClose = (event: React.SyntheticEvent<HTMLElement>) => {
    if (anyChange) {
      setReloading(true);
      window.location.reload();
    } else {
      onClose(event);
    }
  };

  return (
    <>
      <DialogBody>
        <Box padding={{bottom: 8}}>
          <Box padding={{bottom: 8}}>
            <Subheading>Preferences</Subheading>
          </Box>
          <Box
            padding={{bottom: 4, right: 16}}
            flex={{justifyContent: 'space-between', alignItems: 'center'}}
          >
            <Box style={{width: '100%'}}>Timezone</Box>
            <Box style={{display: 'flex', justifyContent: 'flex-end', width: '100%'}}>
              <TimezoneSelect trigger={trigger} />
            </Box>
          </Box>

          <Box
            padding={{bottom: 4, right: 16}}
            flex={{justifyContent: 'space-between', alignItems: 'center'}}
          >
            <Box style={{width: '100%'}}>Hour format</Box>
            <Box style={{display: 'flex', justifyContent: 'flex-end', width: '100%'}}>
              <HourCycleSelect />
            </Box>
          </Box>

          <Box
            padding={{bottom: 4, right: 16}}
            flex={{justifyContent: 'space-between', alignItems: 'center'}}
          >
            <Box style={{width: '100%'}}>
              <span>Theme (</span>
              <a
                href="https://github.com/dagster-io/dagster/discussions/18439"
                target="_blank"
                rel="noreferrer"
              >
                Learn more
              </a>
              )
            </Box>
            <Box style={{display: 'flex', justifyContent: 'flex-end', width: '100%'}}>
              <ThemeSelect theme={theme} onChange={setTheme} />
            </Box>
          </Box>

          <Box
            padding={{vertical: 8, right: 16}}
            flex={{justifyContent: 'space-between', alignItems: 'center'}}
          >
            <Box style={{width: '100%'}}>Enable keyboard shortcuts</Box>
            <Box style={{display: 'flex', justifyContent: 'flex-end', width: '100%'}}>
              <Checkbox
                checked={shortcutsEnabled}
                format="switch"
                onChange={toggleKeyboardShortcuts}
              />
            </Box>
          </Box>
        </Box>
        <Box padding={{top: 16}} border="top">
          <Box padding={{bottom: 8}}>
            <Subheading>Experimental features</Subheading>
          </Box>
          <MetadataTable
            rows={visibleFlags.map(({key, label, flagType}) => ({
              key,
              label,
              value: (
                <Checkbox
                  format="switch"
                  checked={flags.includes(flagType)}
                  onChange={() => toggleFlag(flagType)}
                />
              ),
            }))}
          />
        </Box>
      </DialogBody>
      <DialogFooter topBorder>
        <Button intent="primary" onClick={handleClose} disabled={reloading}>
          Done
        </Button>
      </DialogFooter>
    </>
  );
};
