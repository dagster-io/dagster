import {
  Box,
  Button,
  ButtonLink,
  Checkbox,
  Dialog,
  DialogBody,
  DialogFooter,
  MetadataTable,
  Subheading,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

import {FeatureFlagType, getFeatureFlags, setFeatureFlags} from './Flags';
import {SHORTCUTS_STORAGE_KEY} from './ShortcutHandler';
import {HourCycleSelect} from './time/HourCycleSelect';
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

  const initialFlagState = React.useRef(JSON.stringify([...getFeatureFlags().sort()]));
  const initialShortcutsEnabled = React.useRef(shortcutsEnabled);

  React.useEffect(() => {
    setFeatureFlags(flags);
  });

  const toggleFlag = (flag: FeatureFlagType) => {
    setFlags(flags.includes(flag) ? flags.filter((f) => f !== flag) : [...flags, flag]);
  };

  const trigger = React.useCallback(
    (timezone: string) => (
      <ButtonLink>{timezone === 'Automatic' ? automaticLabel() : timezone}</ButtonLink>
    ),
    [],
  );

  const toggleKeyboardShortcuts = (e: React.ChangeEvent<HTMLInputElement>) => {
    const {checked} = e.target;
    setShortcutsEnabled(checked);
  };

  const anyChange =
    initialFlagState.current !== JSON.stringify([...flags.sort()]) ||
    initialShortcutsEnabled.current !== shortcutsEnabled;

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
          <MetadataTable
            rows={[
              {
                key: 'Timezone',
                value: (
                  <Box margin={{bottom: 4}}>
                    <TimezoneSelect trigger={trigger} />
                  </Box>
                ),
              },
              {
                key: 'Hour format',
                value: (
                  <Box margin={{bottom: 4}}>
                    <HourCycleSelect />
                  </Box>
                ),
              },
              {
                key: 'Enable keyboard shortcuts',
                value: (
                  <Checkbox
                    checked={shortcutsEnabled}
                    format="switch"
                    onChange={toggleKeyboardShortcuts}
                  />
                ),
              },
            ]}
          />
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
