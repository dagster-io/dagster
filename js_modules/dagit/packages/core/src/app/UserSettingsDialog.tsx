import {
  Box,
  Button,
  ButtonLink,
  Checkbox,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  MetadataTable,
  MetadataTableRow,
  Subheading,
  Tooltip,
} from '@dagster-io/ui';
import * as React from 'react';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

import {AppContext} from './AppContext';
import {CodeLinkProtocolSelect} from './CodeLinkProtocol';
import {FeatureFlagType, getFeatureFlags, setFeatureFlags} from './Flags';
import {SHORTCUTS_STORAGE_KEY} from './ShortcutHandler';
import {TimezoneSelect} from './time/TimezoneSelect';
import {automaticLabel} from './time/browserTimezone';

type OnCloseFn = (event: React.SyntheticEvent<HTMLElement>) => void;
type VisibleFlag = {key: string; flagType: FeatureFlagType};

interface DialogProps {
  isOpen: boolean;
  onClose: OnCloseFn;
  visibleFlags: VisibleFlag[];
}

export const UserSettingsDialog: React.FC<DialogProps> = ({isOpen, onClose, visibleFlags}) => {
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
  visibleFlags: {key: string; flagType: FeatureFlagType}[];
}

/**
 * Separate the content from the `Dialog` so that we don't prepare its state before
 * we want to render it.
 */
export const UserSettingsDialogContent: React.FC<DialogContentProps> = ({
  onClose,
  visibleFlags,
}) => {
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

  let experimentalRows: MetadataTableRow[] = visibleFlags.map(({key, flagType}) => ({
    key,
    value: (
      <Checkbox
        format="switch"
        checked={flags.includes(flagType)}
        onChange={() => toggleFlag(flagType)}
      />
    ),
  }));

  const {codeLinksEnabled, telemetryEnabled} = React.useContext(AppContext);

  if (codeLinksEnabled) {
    experimentalRows = experimentalRows.concat([
      {
        key: 'Code link protocol',
        label: (
          <Box margin={{top: 8}} flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            Code link protocol
            <Tooltip
              content={
                <>
                  URL protocol to use when linking to definitions in code
                  <br /> <br />
                  {'{'}FILE{'}'} and {'{'}LINE{'}'} replaced by filepath and line
                  <br />
                  number, respectively
                </>
              }
            >
              <Icon name="info" color={Colors.Gray600} />
            </Tooltip>
          </Box>
        ),
        value: (
          <Box margin={{bottom: 4}}>
            <CodeLinkProtocolSelect />
          </Box>
        ),
      },
    ]);
  }

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
        <Box padding={{top: 16}} border={{side: 'top', width: 1, color: Colors.KeylineGray}}>
          <Box padding={{bottom: 8}}>
            <Subheading>Experimental features</Subheading>
          </Box>
          <MetadataTable rows={experimentalRows} />
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
