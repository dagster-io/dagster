import {Alert, Box, Button} from '@dagster-io/ui-components';
import {useCallback, useContext, useState} from 'react';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {AppContext} from '../app/AppContext';
import {getFeatureFlagsWithoutDefaultValues, setFeatureFlags} from '../app/Flags';
import {useTrackEvent} from '../app/analytics';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

export const BANNER_HIDDEN_KEY = 'dagster.observe-rollout-banner-hidden';
export const OBSERVE_ROLLOUT_ENABLED_TIME_KEY = 'dagster.observe-rollout-enabled-time';

type BannerState = 'show-banner' | 'enabling' | 'hide-banner';

export const ObserveRolloutBanner = () => {
  const trackEvent = useTrackEvent();
  const {basePath} = useContext(AppContext);

  const validate = useCallback((value: any) => value === true, []);
  const [hiddenStorage, setHiddenStorage] = useStateWithStorage(BANNER_HIDDEN_KEY, validate);
  const [enabledState, setEnabledState] = useState<BannerState>(() =>
    hiddenStorage ? 'hide-banner' : 'show-banner',
  );

  const onClick = useCallback(() => {
    trackEvent('feature-flag', {flag: FeatureFlag.flagUseNewObserveUIs, enabled: true});
    setFeatureFlags({
      ...getFeatureFlagsWithoutDefaultValues(),
      [FeatureFlag.flagUseNewObserveUIs]: true,
    });
    localStorage.setItem(OBSERVE_ROLLOUT_ENABLED_TIME_KEY, `${Date.now()}`);
    setEnabledState('enabling');
    window.location.href = `${basePath}/`;
  }, [trackEvent, basePath]);

  const onHide = useCallback(() => {
    setHiddenStorage(true);
    setEnabledState('hide-banner');
  }, [setHiddenStorage]);

  if (enabledState === 'hide-banner') {
    return null;
  }

  return (
    <Box padding={{top: 8, horizontal: 20}}>
      <Alert
        title="You're invited to the early access of the new Dagster+ UI, with a focus on health and observability."
        description={
          <>
            Try it out and share your feedback. You can also enable the new UI later via User
            Settings.{' '}
            <a
              href="https://docs.dagster.io/guides/labs/observability-update"
              target="_blank"
              rel="noreferrer"
            >
              View docs
            </a>
          </>
        }
        rightButton={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}} padding={{left: 12}}>
            <Button onClick={onHide} disabled={enabledState === 'enabling'}>
              Not now
            </Button>
            <Button onClick={onClick} intent="primary" disabled={enabledState === 'enabling'}>
              Enable new UI
            </Button>
          </Box>
        }
      />
    </Box>
  );
};
