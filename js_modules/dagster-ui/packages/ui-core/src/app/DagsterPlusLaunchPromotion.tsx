import {Body1, Box, Button, Dialog, ExternalAnchorButton, Icon} from '@dagster-io/ui-components';
import styled from 'styled-components';

import dagster_plus from './dagster_plus.png';
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
  return (
    <Dialog
      isOpen={!didDismissPromotion}
      onClose={() => {
        setDidDismissPromotion(true);
      }}
      canOutsideClickClose
      canEscapeKeyClose
      style={{width: 800, maxWidth: '80%'}}
    >
      <ImageWrapper>
        <img src={dagster_plus.src} />
      </ImageWrapper>
      <Box flex={{direction: 'column', alignItems: 'center'}} padding={24}>
        <Header>Introducing Dagster+</Header>
        <Body1>
          Join us on <span style={{fontWeight: 600}}>April 17 at 12 ET</span> for the unveiling of
          the next generation of Dagster Cloud.
        </Body1>
        <Box
          flex={{direction: 'row', alignItems: 'center', justifyContent: 'center', gap: 8}}
          padding={{top: 12}}
        >
          <ExternalAnchorButton
            href="https://dagster.io/events/dagster-plus-launch-event"
            target="_blank"
            rel="noreferrer"
            intent="primary"
            rightIcon={<Icon name="open_in_new" />}
          >
            Learn more
          </ExternalAnchorButton>
          <Button
            onClick={() => {
              setDidDismissPromotion(true);
            }}
          >
            Close
          </Button>
        </Box>
      </Box>
    </Dialog>
  );
};

const Header = styled.div`
  font-size: 32px;
  text-align: center;
  font-style: normal;
  font-weight: 500;
  line-height: normal;
`;

const ImageWrapper = styled.div`
  img {
    max-width: 100%;
  }
}
`;
