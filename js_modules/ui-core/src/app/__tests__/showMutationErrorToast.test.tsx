import {showToast} from '@dagster-io/ui-components';

import {UNAUTHORIZED_MUTATION_MESSAGE, showMutationErrorToast} from '../showMutationErrorToast';

jest.mock('@dagster-io/ui-components', () => ({
  ...jest.requireActual('@dagster-io/ui-components'),
  showToast: jest.fn(),
}));

const mockShowToast = showToast as jest.Mock;

type Result =
  | {__typename: 'Sensor'}
  | {__typename: 'UnauthorizedError'; message: string}
  | {__typename: 'SensorNotFoundError'; message: string}
  | {__typename: 'PythonError'; message: string; stack: string[]};

const check = (result: Result | undefined) =>
  showMutationErrorToast(result, 'Sensor', 'Could not save.');

describe('showMutationErrorToast', () => {
  beforeEach(() => {
    mockShowToast.mockClear();
  });

  it('ignores the success type', () => {
    expect(check({__typename: 'Sensor'})).toBe(false);
    expect(mockShowToast).not.toHaveBeenCalled();
  });

  it('treats missing data as a failure', () => {
    expect(check(undefined)).toBe(true);
    expect(mockShowToast).toHaveBeenCalledWith(
      expect.objectContaining({intent: 'danger', message: 'Could not save.'}),
    );
  });

  it('shows a permission message for the default UnauthorizedError', () => {
    expect(check({__typename: 'UnauthorizedError', message: 'Authorization failed'})).toBe(true);
    expect(mockShowToast).toHaveBeenCalledWith(
      expect.objectContaining({message: `Could not save. ${UNAUTHORIZED_MUTATION_MESSAGE}`}),
    );
  });

  it('shows custom UnauthorizedError messages from the server', () => {
    check({__typename: 'UnauthorizedError', message: 'Only available on an Enterprise plan'});
    expect(mockShowToast).toHaveBeenCalledWith(
      expect.objectContaining({message: 'Could not save. Only available on an Enterprise plan'}),
    );
  });

  it('includes the message of other error types', () => {
    expect(check({__typename: 'SensorNotFoundError', message: 'Sensor foo not found'})).toBe(true);
    expect(mockShowToast).toHaveBeenCalledWith(
      expect.objectContaining({message: 'Could not save. Sensor foo not found'}),
    );
  });

  it('offers the stack trace for PythonError', () => {
    expect(check({__typename: 'PythonError', message: 'boom', stack: ['line 1']})).toBe(true);
    expect(mockShowToast).toHaveBeenCalledWith(
      expect.objectContaining({
        message: 'Could not save.',
        action: expect.objectContaining({type: 'button', text: 'View error'}),
      }),
    );
  });
});
