import {ToastConfig, showToast} from '@dagster-io/ui-components';

// todo dish: Remove this, just use `showToast` at callsites directly.
export const showSharedToaster = async (config: ToastConfig) => {
  return showToast(config);
};

export async function copyValue(event: React.MouseEvent<any>, value: string) {
  event.preventDefault();

  const el = document.createElement('textarea');
  document.body.appendChild(el);
  el.value = value;
  el.select();
  document.execCommand('copy');
  el.remove();

  await showSharedToaster({
    message: 'Copied to clipboard!',
    icon: 'copy_to_clipboard_done',
    intent: 'none',
  });
}
