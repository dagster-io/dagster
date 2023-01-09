import {useStateWithStorage} from '@dagster-io/dagit-core/hooks/useStateWithStorage';
import {Dialog} from '@dagster-io/ui';
import React from 'react';
import ReactDOM from 'react-dom';

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

const TIMEOUT = 5000;

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

  const {preloadElement, loaded, renderInto, iframeRef} = useCommuniyNuxIframe({
    height: '462px',
    width: '680px',
  });

  React.useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) {
      return () => {};
    }
    const messageListener = (event: MessageEvent) => {
      switch (event.data) {
        case 'dismiss':
          dismiss();
          break;
      }
    };

    window.addEventListener('message', messageListener);
    return () => {
      window.removeEventListener('message', messageListener, false);
    };
  }, [dismiss, iframeRef]);

  const [target, setTarget] = React.useState<HTMLDivElement | null>(null);
  React.useEffect(() => {
    if (shouldShowNux && loaded && target) {
      renderInto(target);
    }
  }, [shouldShowNux, loaded, renderInto, target]);

  return (
    <>
      <Dialog
        isOpen={shouldShowNux && loaded}
        style={{width: '680px', background: 'transparent', overflow: 'hidden', height: '462px'}}
        transitionDuration={0}
      >
        <div
          ref={(element: HTMLDivElement) => {
            setTarget(element);
          }}
        />
      </Dialog>
      {/** We create a portal after the dialog so that the dialog can be positioned over the blueprint overlay */}
      {ReactDOM.createPortal(preloadElement, document.body)}
    </>
  );
};

const IFRAME_SRC = 'http://dagster.io/dagit_iframes/community_nux';

type Props = {
  width: string;
  height: string;
};

/**
 * This iframe uses a bit of a hack to allow us to show the dialog only when the iframe is fully loaded.
 * To do this we render the iframe offscreen then move it on screen. The problem we run into is two fold:
 *  1) The container we render the iframe into will not be on screen until the iframe is ready, so the iframe can't be initially
 *     put into its final location
 *  2) If we move an iframe's DOM node then the iframe gets reloaded from scratch defeating the purpose of preloading it
 *
 * So instead we position the iframe absolutely and keep track of the position of the target element where we want the iframe to live.
 *
 */
const useCommuniyNuxIframe = ({width, height}: Props) => {
  const iframeRef = React.useRef<HTMLIFrameElement>(null);
  const [loaded, setLoaded] = React.useState(false);
  const [parentRect, setParentRect] = React.useState<DOMRect | null>(null);
  const [parent, setParent] = React.useState<HTMLElement | null>(null);

  React.useLayoutEffect(() => {
    if (parent?.parentNode) {
      const dialogFrame = parent.parentNode as HTMLDivElement;

      const RO = window['ResizeObserver'] as any;
      const observer = new RO(() => {
        setParentRect(dialogFrame.getBoundingClientRect());
      });
      observer.observe(parent.parentNode);
      observer.observe(document.documentElement);
      setParentRect(dialogFrame.getBoundingClientRect());
    }
  }, [parent]);

  return {
    preloadElement: (
      <iframe
        style={
          parentRect
            ? {
                width,
                height,
                position: 'absolute',
                left: parentRect.left,
                top: parentRect.top,
                zIndex: 21,
              }
            : {width, height, left: '-999999px', position: 'absolute', zIndex: 0}
        }
        src={IFRAME_SRC}
        ref={iframeRef}
        onLoad={() => {
          setLoaded(true);
        }}
      />
    ),
    loaded,
    iframeRef,
    renderInto: React.useCallback((parent: HTMLElement) => {
      setParent(parent);
    }, []),
  };
};
