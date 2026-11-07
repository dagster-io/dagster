import {showToast} from '@dagster-io/ui-components';

import {showCustomAlert} from './CustomAlertProvider';
import {GenericError, PythonErrorInfo} from './PythonErrorInfo';

type MutationResult = {__typename: string} & Partial<GenericError>;

export const UNAUTHORIZED_MUTATION_MESSAGE = 'You do not have permission to do this.';

// The backend's default UnauthorizedError message; custom messages are shown as-is.
const DEFAULT_UNAUTHORIZED_MESSAGE = 'Authorization failed';

/**
 * Shows an error toast unless the mutation result is `successTypename`. Missing data counts as a
 * failure. Returns true if an error was shown, so callers can bail out of follow-up work.
 */
export const showMutationErrorToast = <T extends MutationResult>(
  result: T | null | undefined,
  successTypename: T['__typename'],
  failureMessage: string,
): boolean => {
  if (result?.__typename === successTypename) {
    return false;
  }

  if (result?.__typename === 'PythonError') {
    const error: GenericError = {
      message: result.message ?? '',
      stack: result.stack,
      errorChain: result.errorChain,
    };
    showToast({
      intent: 'danger',
      icon: 'error',
      message: failureMessage,
      action: {
        type: 'button',
        text: 'View error',
        onClick: () =>
          showCustomAlert({title: failureMessage, body: <PythonErrorInfo error={error} />}),
      },
    });
    return true;
  }

  const detail =
    result?.__typename === 'UnauthorizedError' &&
    (!result.message || result.message === DEFAULT_UNAUTHORIZED_MESSAGE)
      ? UNAUTHORIZED_MUTATION_MESSAGE
      : result?.message;
  showToast({
    intent: 'danger',
    icon: 'error',
    message: detail ? `${failureMessage} ${detail}` : failureMessage,
  });
  return true;
};
