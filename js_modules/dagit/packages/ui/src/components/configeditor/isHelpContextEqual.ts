import {ConfigEditorHelpContext} from './ConfigEditorHelpContext';

export const isHelpContextEqual = (
  prev: ConfigEditorHelpContext | null,
  next: ConfigEditorHelpContext | null,
) => (prev && prev.type.key) === (next && next.type.key);
