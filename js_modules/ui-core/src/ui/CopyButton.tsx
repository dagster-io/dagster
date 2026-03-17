import {Button, Colors, Icon, UnstyledButton, showToast} from '@dagster-io/ui-components';
import React from 'react';

import {useCopyToClipboard} from '../app/browser';

interface CopyIconButtonProps {
  value: string | (() => string);
  iconSize?: 12 | 16 | 20 | 24;
  iconColor?: string;
}

export const CopyIconButton = ({
  value,
  iconSize = 16,
  iconColor = Colors.accentGray(),
}: CopyIconButtonProps) => {
  const copyToClipboard = useCopyToClipboard();
  const [didCopy, setDidCopy] = React.useState(false);
  const iconTimeout = React.useRef<ReturnType<typeof setTimeout>>();

  const performCopy = React.useCallback(async () => {
    if (iconTimeout.current) {
      clearTimeout(iconTimeout.current);
    }

    copyToClipboard(value instanceof Function ? value() : value);

    showToast({
      icon: 'copy_to_clipboard_done',
      message: 'Copied!',
      intent: 'success',
    });

    setDidCopy(true);
    iconTimeout.current = setTimeout(() => {
      setDidCopy(false);
    }, 2000);
  }, [value, copyToClipboard]);

  return (
    <UnstyledButton $expandedClickPx={6} onClick={performCopy}>
      <Icon
        name={didCopy ? 'copy_to_clipboard_done' : 'copy_to_clipboard'}
        color={iconColor}
        size={iconSize}
      />
    </UnstyledButton>
  );
};

export const CopyButton = ({
  value,
  children,
}: {
  value: string | (() => string);
  children: React.ReactNode;
}) => {
  const copyToClipboard = useCopyToClipboard();
  return (
    <Button
      autoFocus={false}
      onClick={async () => {
        copyToClipboard(value instanceof Function ? value() : value);
        showToast({
          icon: 'copy_to_clipboard_done',
          intent: 'success',
          message: 'Copied!',
        });
      }}
    >
      {children}
    </Button>
  );
};
