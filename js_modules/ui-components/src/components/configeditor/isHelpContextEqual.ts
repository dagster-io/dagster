import {ConfigEditorHelpContext} from './types/ConfigEditorHelpContext';

export const isHelpContextEqual = (
  prev: ConfigEditorHelpContext | null,
  next: ConfigEditorHelpContext | null,
) => {
  if (!prev || !next) {
    return prev === next;
  }
  return prev.type.key === next.type.key && prev.path.length === next.path.length && prev.path.every((p, i) => p === next.path[i]);
};
