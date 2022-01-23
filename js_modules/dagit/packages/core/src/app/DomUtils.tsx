import {Toaster} from '@dagster-io/ui';

export const SharedToaster = Toaster.create({position: 'top'}, document.body);

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
    icon: 'copy_to_clipboard_done',
    intent: 'none',
  });
}
