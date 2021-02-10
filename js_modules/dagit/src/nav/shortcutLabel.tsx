import {KeyShortcut} from 'src/nav/config';

export const shortcutLabel = (shortcut: KeyShortcut) => {
  const {code, modifier} = shortcut;

  const ascii = code.replace(/(Key)|(Digit)/, '');
  const modKey = () => {
    switch (modifier) {
      case 'Alt':
        return '⌥';
      case null:
      case undefined:
        return '';
      default:
        return '?';
    }
  };

  return `${modKey()}${ascii}`;
};
