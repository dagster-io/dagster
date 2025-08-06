import {Box, Button, Checkbox, Icon, Subheading, Tooltip} from '@dagster-io/ui-components';
import React from 'react';

import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {SHORTCUTS_STORAGE_KEY} from '../ShortcutHandler';
import {HourCycleSelect} from '../time/HourCycleSelect';
import {ThemeSelect} from '../time/ThemeSelect';
import {TimezoneSelect} from '../time/TimezoneSelect';
import {automaticLabel} from '../time/browserTimezone';
import {useThemeState} from '../useThemeState';
import {useShowAssetsWithoutDefinitions} from './useShowAssetsWithoutDefinitions';
import {useShowStubAssets} from './useShowStubAssets';

export const UserPreferences = ({
  onChangeRequiresReload,
}: {
  onChangeRequiresReload: (requiresReload: boolean) => void;
}) => {
  const [shortcutsEnabled, setShortcutsEnabled] = useStateWithStorage(
    SHORTCUTS_STORAGE_KEY,
    (value: any) => (typeof value === 'boolean' ? value : true),
  );
  const {showAssetsWithoutDefinitions, setShowAssetsWithoutDefinitions} =
    useShowAssetsWithoutDefinitions();
  const {showStubAssets, setShowStubAssets} = useShowStubAssets();
  const {theme, setTheme} = useThemeState();

  const initialShortcutsEnabled = React.useRef(shortcutsEnabled);

  const lastChangeValue = React.useRef(false);
  React.useEffect(() => {
    const didChange = initialShortcutsEnabled.current !== shortcutsEnabled;
    if (lastChangeValue.current !== didChange) {
      onChangeRequiresReload(didChange);
      lastChangeValue.current = didChange;
    }
  }, [shortcutsEnabled, theme, onChangeRequiresReload]);

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

  const toggleShowAssetsWithoutDefinitions = (e: React.ChangeEvent<HTMLInputElement>) => {
    const {checked} = e.target;
    setShowAssetsWithoutDefinitions(checked);
  };

  const toggleShowStubAssets = (e: React.ChangeEvent<HTMLInputElement>) => {
    const {checked} = e.target;
    setShowStubAssets(checked);
  };

  return (
    <>
      <Box padding={{bottom: 4}}>
        <Subheading>Preferences</Subheading>
      </Box>
      <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <div>Timezone</div>
        <TimezoneSelect trigger={trigger} />
      </Box>
      <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <div>Hour format</div>
        <HourCycleSelect />
      </Box>
      <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <div>Theme</div>
        <ThemeSelect theme={theme} onChange={setTheme} />
      </Box>
      <Box padding={{vertical: 8}} flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <div>Enable keyboard shortcuts</div>
        <Checkbox checked={shortcutsEnabled} format="switch" onChange={toggleKeyboardShortcuts} />
      </Box>
      <Box padding={{vertical: 8}} flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <Box flex={{direction: 'row', alignItems: 'center'}}>
          <div>Show assets without definitions in catalog</div>
          <Tooltip content="Hide assets that lack current code definitions (typically legacy or orphaned assets with only historical materialization data) helping users focus on actively managed assets">
            <Icon name="info" />
          </Tooltip>
        </Box>
        <Checkbox
          checked={showAssetsWithoutDefinitions}
          format="switch"
          onChange={toggleShowAssetsWithoutDefinitions}
        />
      </Box>
      <Box padding={{vertical: 8}} flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <Box flex={{direction: 'row', alignItems: 'center'}}>
          <div>Show stub assets in Catalog</div>
          <Tooltip content="Stub assets are placeholder assets that Dagster automatically creates to represent dependencies that aren't defined in your current code location. ">
            <Icon name="info" />
          </Tooltip>
        </Box>
        <Checkbox checked={showStubAssets} format="switch" onChange={toggleShowStubAssets} />
      </Box>
    </>
  );
};
