import * as React from 'react';
import {Button, Intent, Menu} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import {Select} from '@blueprintjs/select';
import {ModeNotFoundError} from './ExecutionSessionContainer';

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

const ModeSelect = Select.ofType<Mode>();

export const ConfigEditorModePicker: React.FunctionComponent<ConfigEditorModePickerProps> = (
  props,
) => {
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
    <ModeSelect
      activeItem={resolvedMode}
      filterable={true}
      disabled={singleMode && valid}
      items={props.modes}
      itemPredicate={(query, mode) => query.length === 0 || mode.name.includes(query)}
      itemRenderer={(mode, props) => (
        <Menu.Item
          active={props.modifiers.active}
          key={mode.name}
          text={mode.name}
          onClick={props.handleClick}
        />
      )}
      onItemSelect={onItemSelect}
    >
      <Button
        icon={valid ? undefined : IconNames.ERROR}
        intent={valid ? Intent.NONE : Intent.DANGER}
        title={disabled ? MODE_PICKER_HINT_TEXT : 'Current execution mode'}
        text={
          valid
            ? resolvedMode
              ? `Mode: ${resolvedMode.name}`
              : 'Select Mode'
            : 'Invalid Mode Selection'
        }
        disabled={disabled}
        rightIcon="caret-down"
        data-test-id="mode-picker-button"
      />
    </ModeSelect>
  );
};
