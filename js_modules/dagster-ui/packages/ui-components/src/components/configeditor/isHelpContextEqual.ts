import {ConfigEditorHelpContext} from './types/ConfigEditorHelpContext';

export const isHelpContextEqual = (
  prev: ConfigEditorHelpContext | null,
  next: ConfigEditorHelpContext | null,
) => {
  if (!prev || !next) return prev === next;
  return prev.type.key === next.type.key && JSON.stringify(prev.path) === JSON.stringify(next.path);
};
