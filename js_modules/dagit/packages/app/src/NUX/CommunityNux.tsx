import {useStateWithStorage} from '@dagster-io/dagit-core/hooks/useStateWithStorage';
import React from 'react';
import ReactDOM from 'react-dom';
import {createGlobalStyle} from 'styled-components/macro';

export const CommunityNux = () => {
  const [didDismissCommunityNux, dismissCommunityNux] = useStateWithStorage(
    'communityNux',
    (data) => data,
  );
  if (didDismissCommunityNux) {
    return null;
  }
  return (
    <CommunityNuxImpl
      dismiss={() => {
        dismissCommunityNux('1');
      }}
    />
  );
};

// Wait 1 second before trying to show Nux
const TIMEOUT = 1000;

const CommunityNuxImpl: React.FC<{dismiss: () => void}> = ({dismiss}) => {
  const [shouldShowNux, setShouldShowNux] = React.useState(false);
  React.useEffect(() => {
    const timeout = setTimeout(() => {
      setShouldShowNux(true);
    }, TIMEOUT); // wait 5 seconds before showing Nux
    return () => {
      clearTimeout(timeout);
    };
  }, []);

  const [iframeLoaded, setIframeLoaded] = React.useState(false);
  const [width, setWidth] = React.useState(680);
  const [height, setHeight] = React.useState(462);

  React.useEffect(() => {
    const messageListener = (event: MessageEvent) => {
      if (event.data === 'dismiss') {
        dismiss();
      } else if (event.data?.startsWith?.('dimensions_')) {
        const [_, width, height] = event.data.split('_');
        setHeight(Math.ceil(height));
        setWidth(Math.ceil(width));
      }
    };

    window.addEventListener('message', messageListener);
    return () => {
      window.removeEventListener('message', messageListener, false);
    };
  }, [dismiss]);

  const isOpen = shouldShowNux && iframeLoaded;

  return ReactDOM.createPortal(
    <div className="bp3-portal dagit-portal">
      <GlobalOffscreenStyle />
      <div
        className={`bp3-overlay ${isOpen ? 'bp3-overlay-open' : ''} bp3-overlay-scroll-container`}
      >
        {isOpen ? <div className="bp3-overlay-backdrop dagit-backdrop" /> : null}
        <div className="bp3-dialog-container bp3-overlay-content">
          <div
            className={`bp3-dialog dagit-dialog ${isOpen ? '' : 'offscreen'}`}
            style={{width: width + 'px', height: height + 'px'}}
          >
            <iframe
              src={IFRAME_SRC}
              width={width}
              height={height}
              style={{
                border: 'none',
              }}
              onLoad={() => {
                setIframeLoaded(true);
              }}
            />
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
};

const IFRAME_SRC = 'https://dagster.io/dagit_iframes/community_nux';

const GlobalOffscreenStyle = createGlobalStyle`
  .offscreen {
    position: absolute;
    left: -99999px;
  }
`;
