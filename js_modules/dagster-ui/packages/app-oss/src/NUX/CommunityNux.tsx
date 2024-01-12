import {gql, useMutation, useQuery} from '@apollo/client';
import {
  Body,
  Box,
  Button,
  Checkbox,
  Colors,
  Dialog,
  ExternalAnchorButton,
  Heading,
  Icon,
  Spinner,
  TextInput,
} from '@dagster-io/ui-components';
import {useStateWithStorage} from '@dagster-io/ui-core/hooks/useStateWithStorage';
import React from 'react';
import isEmail from 'validator/lib/isEmail';

export const CommunityNux = () => {
  const [didDismissCommunityNux, dissmissInBrowser] = useStateWithStorage(
    'communityNux',
    (data) => data,
  );
  const {data, loading} = useQuery(GET_SHOULD_SHOW_NUX_QUERY);
  const [dismissOnServer] = useMutation(SET_NUX_SEEN_MUTATION);

  if (!isLocalhost()) {
    // Yes, we only want to show this on localhost for now.
    return null;
  }
  if (didDismissCommunityNux || loading || (data && !data.shouldShowNux)) {
    return null;
  }
  return (
    <CommunityNuxImpl
      dismiss={() => {
        dissmissInBrowser('1');
        dismissOnServer();
      }}
    />
  );
};

// Wait 1 second before trying to show Nux
const TIMEOUT = 1000;

const CommunityNuxImpl = ({dismiss}: {dismiss: () => void}) => {
  const [shouldShowNux, setShouldShowNux] = React.useState(false);
  React.useEffect(() => {
    const timeout = setTimeout(() => {
      setShouldShowNux(true);
    }, TIMEOUT);
    return () => {
      clearTimeout(timeout);
    };
  }, []);

  const [iframeData, setIframeData] = React.useState<{email: string; newsletter: boolean} | null>(
    null,
  );
  const submit = (email: string, newsletter: boolean) => {
    setIframeData({email, newsletter});
  };

  return (
    <Dialog isOpen={shouldShowNux} style={{width: '680px'}}>
      {iframeData ? (
        <RecaptchaIFrame
          email={iframeData.email}
          newsletter={iframeData.newsletter}
          dismiss={dismiss}
        />
      ) : (
        <Form dismiss={dismiss} submit={submit} />
      )}
    </Dialog>
  );
};

interface FormProps {
  dismiss: () => void;
  submit: (email: string, newsletter: boolean) => void;
}

const Form = ({dismiss, submit}: FormProps) => {
  const [email, setEmail] = React.useState('');
  const [newsletter, setNewsLetter] = React.useState(false);
  const validEmail = isEmail(email);
  const [emailChanged, setEmailChanged] = React.useState(false);
  const [blurred, setBlurred] = React.useState(false);

  return (
    <Box
      flex={{direction: 'column', gap: 16}}
      style={{padding: '36px', width: '680px', background: Colors.backgroundDefault()}}
    >
      <Box
        flex={{direction: 'row', gap: 24, alignItems: 'center'}}
        padding={{bottom: 24}}
        border="bottom"
      >
        <Box flex={{direction: 'column', gap: 8, alignItems: 'start', justifyContent: 'start'}}>
          <Heading>Join the Dagster community</Heading>
          <Body style={{color: Colors.textLight(), marginBottom: '4px'}}>
            Connect with thousands of other data practitioners building with Dagster. Share
            knowledge, get help, and contribute to the open-source project.
          </Body>
          <ExternalAnchorButton
            icon={<Icon name="slack" />}
            href="https://www.dagster.io/slack?utm_source=local-nux"
          >
            Join us on Slack
          </ExternalAnchorButton>
        </Box>
        <video autoPlay muted loop playsInline width={120} height={120}>
          <source src={`${process.env.PUBLIC_URL}/Dagster_world.mp4`} type="video/mp4" />
        </video>
      </Box>
      <Box flex={{direction: 'column', justifyContent: 'stretch', gap: 12}}>
        <div>Notify me about Dagster security updates</div>
        <TextInput
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            setEmailChanged(true);
          }}
          onBlur={() => setBlurred(true)}
          placeholder="hello@dagster.io"
          strokeColor={!emailChanged || validEmail ? undefined : Colors.accentRed()}
          style={{width: '100%'}}
        />
        {emailChanged && blurred && !validEmail ? (
          <div style={{paddingBottom: '12px', color: Colors.textRed(), fontSize: '12px'}}>
            Add your email to get updates from Dagster.
          </div>
        ) : null}
        <Box as="label" flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <Checkbox
            checked={newsletter}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              setNewsLetter(e.target.checked);
            }}
          />{' '}
          <span>Sign up for the Dagster newsletter</span>
        </Box>
      </Box>
      <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
        <a href="https://dagster.io/privacy" target="_blank" rel="noreferrer">
          Privacy Policy
        </a>
        <Box flex={{direction: 'row', gap: 8}}>
          <Button
            onClick={() => {
              dismiss();
            }}
          >
            Skip
          </Button>
          <Button
            onClick={() => {
              submit(email, newsletter);
            }}
            disabled={!validEmail}
            intent="primary"
          >
            Submit
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

interface RecaptchaIFrameProps {
  newsletter: boolean;
  email: string;
  dismiss: () => void;
}

const RecaptchaIFrame = ({dismiss, newsletter, email}: RecaptchaIFrameProps) => {
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

  return (
    <Box padding={32} flex={{justifyContent: 'center', alignItems: 'center'}}>
      {iframeLoaded ? null : <Spinner purpose="section" />}
      <iframe
        src={`${IFRAME_SRC}?email=${email}${newsletter ? '&newsletter=1' : ''}`}
        width={width}
        height={height}
        style={{
          border: 'none',
          overflow: 'hidden',
          ...(iframeLoaded
            ? {}
            : {
                position: 'absolute',
                left: '-99999px',
                width: '304px',
                height: '78px',
              }),
        }}
        scrolling="no"
        onLoad={() => {
          setIframeLoaded(true);
        }}
      />
    </Box>
  );
};

const IFRAME_SRC = '//dagster.io/dagit_iframes/community_nux';

const SET_NUX_SEEN_MUTATION = gql`
  mutation SetNuxSeen {
    setNuxSeen
  }
`;

const GET_SHOULD_SHOW_NUX_QUERY = gql`
  query ShouldShowNux {
    shouldShowNux
  }
`;

function isLocalhost() {
  const origin = window.location.origin;
  return origin.startsWith('http://127.0.0.1') || origin.startsWith('http://localhost');
}
