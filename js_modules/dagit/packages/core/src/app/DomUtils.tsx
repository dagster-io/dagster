import {Intent, Position, Toaster} from '@blueprintjs/core';

export const SharedToaster = Toaster.create({position: Position.TOP}, document.body);

export async function copyValue(event: React.MouseEvent<any>, value: string) {
  event.preventDefault();

  const el = document.createElement('textarea');
  document.body.appendChild(el);
  el.value = value;
  el.select();
  document.execCommand('copy');
  el.remove();

  SharedToaster.show({
    message: 'Copied to clipboard!',
    icon: 'clipboard',
    intent: Intent.NONE,
  });
}
