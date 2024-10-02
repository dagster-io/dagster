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
  Subheading,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import {UserPreferences} from 'shared/app/UserSettingsDialog/UserPreferences.oss';

import {CodeLinkProtocolSelect} from '../../code-links/CodeLinkProtocol';
import {showCustomAlert} from '../CustomAlertProvider';
import {getFeatureFlags, setFeatureFlags} from '../Flags';
import {useTrackEvent} from '../analytics';

type OnCloseFn = (event: React.SyntheticEvent<HTMLElement>) => void;
type VisibleFlag = {key: string; label?: React.ReactNode; flagType: FeatureFlag};

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
  visibleFlags: {key: string; label?: React.ReactNode; flagType: FeatureFlag}[];
}

/**
 * Separate the content from the `Dialog` so that we don't prepare its state before
 * we want to render it.
 */
const UserSettingsDialogContent = ({onClose, visibleFlags}: DialogContentProps) => {
  const trackEvent = useTrackEvent();
  const [flags, setFlags] = React.useState<FeatureFlag[]>(() => getFeatureFlags());
  const [reloading, setReloading] = React.useState(false);

  const initialFlagState = React.useRef(JSON.stringify([...getFeatureFlags().sort()]));

  React.useEffect(() => {
    setFeatureFlags(flags);
  });

  const toggleFlag = (flag: FeatureFlag) => {
    const flagSet = new Set(flags);
    trackEvent('feature-flag', {flag, enabled: !flagSet.has(flag)});
    if (flagSet.has(flag)) {
      flagSet.delete(flag);
    } else {
      flagSet.add(flag);
    }
    setFlags(Array.from(flagSet));
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
        <Box padding={{vertical: 16}} border="top">
          <Box padding={{bottom: 8}}>
            <Subheading>Experimental features</Subheading>
          </Box>
          {experimentalSettings}
        </Box>
        <Box padding={{top: 16}} border="top">
          <ButtonLink
            onClick={() => {
              indexedDB.databases().then((databases) => {
                databases.forEach((db) => {
                  db.name && indexedDB.deleteDatabase(db.name);
                });
              });
              showCustomAlert({
                title: 'Caches reset',
                body: (
                  <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                    IndexedDB cache has been reset.
                    <ButtonLink
                      onClick={() => {
                        window.location.reload();
                      }}
                    >
                      Click here to reload the page
                    </ButtonLink>
                  </Box>
                ),
              });
            }}
          >
            <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
              Reset IndexedDB cache
              <Tooltip content="If you're seeing stale definitions or experiencing client side bugs then this may fix it">
                <Icon name="info" />
              </Tooltip>
            </Box>
          </ButtonLink>
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
