import {ButtonWIP, IconWIP, MenuItemWIP, SelectWIP} from '@dagster-io/ui';
import * as React from 'react';

import {ModeNotFoundError} from './ModeNotFoundError';

interface Mode {
  name: string;
}

interface ConfigEditorModePickerProps {
  modes: Mode[];
  modeError?: ModeNotFoundError;
  modeName: string | null;
  onModeChange: (mode: string) => void;
}

const MODE_PICKER_HINT_TEXT = `To add a mode, add a ModeDefinition to the pipeline.`;

export const ConfigEditorModePicker: React.FC<ConfigEditorModePickerProps> = (props) => {
  const resolvedMode = props.modeName
    ? props.modes.find((m) => m.name === props.modeName)
    : props.modes[0];

  React.useEffect(() => {
    if (resolvedMode && resolvedMode.name !== props.modeName) {
      props.onModeChange?.(resolvedMode.name);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolvedMode, props.modeName]);

  const singleMode = props.modes.length === 1;
  const valid = !props.modeError;
  const disabled = singleMode && valid;

  const onItemSelect = (mode: Mode) => {
    props.onModeChange?.(mode.name);
  };

  return (
    <SelectWIP
      activeItem={resolvedMode}
      filterable={true}
      disabled={disabled}
      items={props.modes}
      itemPredicate={(query, mode) => query.length === 0 || mode.name.includes(query)}
      itemRenderer={(mode, props) => (
        <MenuItemWIP
          active={props.modifiers.active}
          key={mode.name}
          text={mode.name}
          onClick={props.handleClick}
        />
      )}
      onItemSelect={onItemSelect}
    >
      <ButtonWIP
        icon={valid ? undefined : <IconWIP name="error" />}
        intent={valid ? 'none' : 'danger'}
        title={disabled ? MODE_PICKER_HINT_TEXT : 'Current execution mode'}
        disabled={disabled}
        rightIcon={<IconWIP name="expand_more" />}
        data-test-id="mode-picker-button"
      >
        {valid
          ? resolvedMode
            ? `Mode: ${resolvedMode.name}`
            : 'Select Mode'
          : 'Invalid Mode Selection'}
      </ButtonWIP>
    </SelectWIP>
  );
};
