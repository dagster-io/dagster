import {render} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {AppContext, AppContextValue} from '../../app/AppContext';
import {
  BANNER_HIDDEN_KEY,
  OBSERVE_ROLLOUT_ENABLED_TIME_KEY,
  ObserveRolloutBanner,
} from '../ObserveRolloutBanner';

const mockTrackEvent = jest.fn();

jest.mock('../../app/analytics', () => ({
  useTrackEvent: jest.fn().mockImplementation(() => mockTrackEvent),
}));

const mockAppContext: AppContextValue = {
  localCacheIdPrefix: 'test',
  basePath: '',
  rootServerURI: '',
  telemetryEnabled: false,
};

describe('ObserveRolloutBanner', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  const Test = () => {
    return (
      <MemoryRouter>
        <AppContext.Provider value={mockAppContext}>
          <ObserveRolloutBanner />
        </AppContext.Provider>
      </MemoryRouter>
    );
  };

  it('should render', async () => {
    const {findByText, findByRole} = render(<Test />);
    expect(await findByText(/you\'re invited/i)).toBeVisible();
    expect(await findByRole('button', {name: /enable new ui/i})).toBeVisible();
    expect(await findByRole('button', {name: /not now/i})).toBeVisible();
  });

  it('should not render if the banner has previously been hidden', async () => {
    window.localStorage.setItem(BANNER_HIDDEN_KEY, 'true');
    const {queryByText} = render(<Test />);
    expect(queryByText(/you\'re invited/i)).not.toBeInTheDocument();
  });

  it('should dismiss the banner when the "Not now" button is clicked', async () => {
    const user = userEvent.setup();
    const {findByRole, queryByText, rerender} = render(<Test />);

    const notNowButton = await findByRole('button', {name: /not now/i});
    expect(notNowButton).toBeVisible();
    await user.click(notNowButton);

    expect(window.localStorage.getItem(BANNER_HIDDEN_KEY)).toBe('true');

    rerender(<Test />);
    expect(queryByText(/you\'re invited/i)).not.toBeInTheDocument();
  });

  it('should enable the new UI when the "Enable new UI" button is clicked', async () => {
    const user = userEvent.setup();
    const {findByRole} = render(<Test />);

    const enableButton = await findByRole('button', {name: /enable new ui/i});
    expect(enableButton).toBeVisible();
    await user.click(enableButton);

    expect(enableButton).toBeDisabled();
    const savedTimeString = window.localStorage.getItem(OBSERVE_ROLLOUT_ENABLED_TIME_KEY);
    const savedTimeNumber = parseInt(savedTimeString ?? '0', 10);
    expect(savedTimeNumber).toBeGreaterThan(0);

    expect(mockTrackEvent).toHaveBeenCalledWith('feature-flag', {
      flag: FeatureFlag.flagUseNewObserveUIs,
      enabled: true,
    });
  });
});
