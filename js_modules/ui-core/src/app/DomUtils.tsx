import {showToast} from '@dagster-io/ui-components';

export async function copyValue(event: React.MouseEvent<any>, value: string) {
  event.preventDefault();

  const el = document.createElement('textarea');
  document.body.appendChild(el);
  el.value = value;
  el.select();
  document.execCommand('copy');
  el.remove();

  showToast({
    message: 'Copied to clipboard!',
    icon: 'copy_to_clipboard_done',
    intent: 'none',
  });
}
