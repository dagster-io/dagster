import {
  Body,
  DagsterTheme,
  Dialog,
  DialogBody,
  DialogFooter,
  ExternalAnchorButton,
  getTheme,
} from '@dagster-io/ui-components';
import styled from 'styled-components';

import dagster_plus_light from './dagster_plus-primary-horizontal.svg';
import dagster_plus_dark from './dagster_plus-reversed-horizontal.svg';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

// April 17th at 12:00 ET
const EVENT_TIME = 1713372960000;

export const DagsterPlusLaunchPromotion = () => {
  const [didDismissPromotion, setDidDismissPromotion] = useStateWithStorage<boolean>(
    'dagster_plus_launch_promotion',
    (json) => !!json,
  );
  if (Date.now() > EVENT_TIME) {
    return null;
  }
  const isDarkMode = getTheme() === DagsterTheme.Dark;
  return (
    <Dialog
      isOpen={!didDismissPromotion}
      onClose={() => {
        setDidDismissPromotion(true);
      }}
      canOutsideClickClose
      canEscapeKeyClose
      title={
        <Header>
          Join us for the unveiling of <span style={{fontWeight: 800}}>Dagster+</span>, the next
          generation of Dagster Cloud.
        </Header>
      }
    >
      <DialogBody>
        <ImageWrapper>
          <img src={isDarkMode ? dagster_plus_dark.src : dagster_plus_light.src} />
        </ImageWrapper>
        <Body className="text-xl font-normal pt-2 text-gable-green md:px-8">
          On <span style={{fontWeight: 600}}>April 17th at 12:00 ET</span> the Dagster Labs team
          will unveil the next generation of Dagster Cloud.
        </Body>
      </DialogBody>
      <DialogFooter topBorder>
        <ExternalAnchorButton
          href="https://dagster.io/events/dagster-plus-launch-event"
          target="_blank"
          rel="noreferrer"
        >
          Learn more
        </ExternalAnchorButton>
      </DialogFooter>
    </Dialog>
  );
};

const Header = styled.div`
  background: linear-gradient(0deg, #4f43dd, #ac00fc 40%, #5756ab);
  background: -webkit-linear-gradient(0deg, #4f43dd, #ac00fc 40%, #5756ab);
  background-clip: text;
  -webkit-background-clip: text;
  color: transparent;
  -webkit-text-fill-color: transparent;
  font-weight: 400;
  font-size: 18px;
  white-space: normal;
`;

const ImageWrapper = styled.div`
  background-attachment: fixed;
  border-radius: 36px;
  padding: 16px 40px;
  img {
    max-height: 176px;
    max-width: 100%;
  }
}
`;
