import {
  Box,
  Button,
  Checkbox,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  Subheading,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {UserPreferences} from './UserPreferences';
import {CodeLinkProtocolSelect} from '../../code-links/CodeLinkProtocol';
import {FeatureFlagType, getFeatureFlags, setFeatureFlags} from '../Flags';

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

  const initialFlagState = React.useRef(JSON.stringify([...getFeatureFlags().sort()]));

  React.useEffect(() => {
    setFeatureFlags(flags);
  });

  const toggleFlag = (flag: FeatureFlagType) => {
    setFlags(flags.includes(flag) ? flags.filter((f) => f !== flag) : [...flags, flag]);
  };

  const [arePreferencesChanged, setAreaPreferencesChanged] = React.useState(false);

  const anyChange =
    initialFlagState.current !== JSON.stringify([...flags.sort()]) || arePreferencesChanged;

  const handleClose = (event: React.SyntheticEvent<HTMLElement>) => {
    if (anyChange) {
      setReloading(true);
      window.location.reload();
    } else {
      onClose(event);
    }
  };

  const experimentalSettings = visibleFlags.map(({key, label, flagType}) => (
    <Box
      padding={{vertical: 8}}
      flex={{justifyContent: 'space-between', alignItems: 'center'}}
      key={key}
    >
      <div>{label || key}</div>
      <Checkbox
        format="switch"
        checked={flags.includes(flagType)}
        onChange={() => toggleFlag(flagType)}
      />
    </Box>
  ));

  experimentalSettings.push(
    <Box
      padding={{vertical: 8}}
      flex={{
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        direction: 'column',
        gap: 8,
      }}
      key="code-link"
    >
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        Editor link protocol
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
          <Icon name="info" color={Colors.accentGray()} />
        </Tooltip>
      </Box>
      <CodeLinkProtocolSelect />
    </Box>,
  );

  return (
    <>
      <DialogBody>
        <Box padding={{bottom: 8}} flex={{direction: 'column', gap: 4}}>
          <UserPreferences onChangeRequiresReload={setAreaPreferencesChanged} />
        </Box>
        <Box padding={{top: 16}} border="top">
          <Box padding={{bottom: 8}}>
            <Subheading>Experimental features</Subheading>
          </Box>
          {experimentalSettings}
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
