import {showToast} from '@dagster-io/ui-components';
import {createMemoryHistory} from 'history';

import {showCustomAlert} from '../../app/CustomAlertProvider';
import {buildLaunchRunSuccess, buildRun} from '../../graphql/builders';
import {handleLaunchResult} from '../RunUtils';

jest.mock('@dagster-io/ui-components', () => ({
  ...jest.requireActual('@dagster-io/ui-components'),
  showToast: jest.fn(),
}));

jest.mock('../../app/CustomAlertProvider', () => ({
  showCustomAlert: jest.fn(),
}));

describe('handleLaunchResult', () => {
  let history: ReturnType<typeof createMemoryHistory>;

  beforeEach(() => {
    history = createMemoryHistory();
    jest.clearAllMocks();
  });

  const successResult = buildLaunchRunSuccess({
    run: buildRun({id: 'abc-123', pipelineName: 'my_job'}),
  });

  describe('openInNewTab', () => {
    it('calls the openInNewTab callback when provided with behavior "open"', async () => {
      const openInNewTab = jest.fn();

      await handleLaunchResult('my_job', successResult, history, {
        behavior: 'open',
        openInNewTab,
      });

      expect(openInNewTab).toHaveBeenCalledWith('/runs/abc-123');
      // Should NOT navigate in the same tab
      expect(history.location.pathname).toBe('/');
    });

    it('calls the openInNewTab callback when provided with behavior "toast"', async () => {
      const openInNewTab = jest.fn();

      await handleLaunchResult('my_job', successResult, history, {
        behavior: 'toast',
        openInNewTab,
      });

      expect(openInNewTab).toHaveBeenCalledWith('/runs/abc-123');
      // Should NOT show a toast when opening in new tab
      expect(showToast).not.toHaveBeenCalled();
    });

    it('navigates in the same tab when openInNewTab is not provided with behavior "open"', async () => {
      await handleLaunchResult('my_job', successResult, history, {
        behavior: 'open',
      });

      expect(history.location.pathname).toBe('/runs/abc-123');
    });

    it('shows a toast when openInNewTab is not provided with behavior "toast"', async () => {
      await handleLaunchResult('my_job', successResult, history, {
        behavior: 'toast',
      });

      expect(history.location.pathname).toBe('/');
      expect(showToast).toHaveBeenCalledWith(expect.objectContaining({intent: 'success'}));
    });

    it('preserves querystring when opening in new tab', async () => {
      history.push({pathname: '/old', search: '?foo=bar'});
      const openInNewTab = jest.fn();

      await handleLaunchResult('my_job', successResult, history, {
        behavior: 'open',
        preserveQuerystring: true,
        openInNewTab,
      });

      expect(openInNewTab).toHaveBeenCalledWith('/runs/abc-123?foo=bar');
    });
  });

  describe('error handling', () => {
    it('shows an alert when result is null', async () => {
      await handleLaunchResult('my_job', null, history, {behavior: 'open'});
      expect(showCustomAlert).toHaveBeenCalled();
    });
  });
});
