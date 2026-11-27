import {showToast} from '@dagster-io/ui-components';

export const showCopySuccessToast = (message: string) =>
  showToast({message, intent: 'success', icon: 'copy_to_clipboard_done'});
