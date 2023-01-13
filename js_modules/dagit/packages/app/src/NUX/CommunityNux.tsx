import {useStateWithStorage} from '@dagster-io/dagit-core/hooks/useStateWithStorage';
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
} from '@dagster-io/ui';
import React from 'react';
import isEmail from 'validator/lib/isEmail';

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

  console.log({iframeData});

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

const Form: React.FC<{
  dismiss: () => void;
  submit: (email: string, newsletter: boolean) => void;
}> = ({dismiss, submit}) => {
  const [email, setEmail] = React.useState('');
  const [newsletter, setNewsLetter] = React.useState(false);
  const validEmail = isEmail(email);
  const [emailChanged, setEmailChanged] = React.useState(false);
  const [blurred, setBlurred] = React.useState(false);

  return (
    <Box
      flex={{direction: 'column', gap: 16}}
      style={{padding: '36px', width: '680px', background: 'white'}}
    >
      <Box
        flex={{direction: 'row', gap: 24, alignItems: 'center'}}
        padding={{bottom: 24}}
        border={{side: 'bottom', color: Colors.KeylineGray, width: 1}}
      >
        <Box flex={{direction: 'column', gap: 8, alignItems: 'start', justifyContent: 'start'}}>
          <Heading>Join the Dagster community</Heading>
          <Body style={{color: Colors.Gray700, marginBottom: '4px'}}>
            Connect with thousands of other data practitioners building with Dagster. Share
            knowledge, get help, and contribute to the open-source project.
          </Body>
          <ExternalAnchorButton icon={<Icon name="slack" />} href="https://www.dagster.io/slack">
            Join us on Slack
          </ExternalAnchorButton>
        </Box>
        <video autoPlay muted loop playsInline width={120} height={120}>
          <source src="/Dagster_world.mp4" type="video/mp4" />
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
          strokeColor={!emailChanged || validEmail ? undefined : Colors.Red500}
          style={{width: '100%'}}
        />
        {emailChanged && blurred && !validEmail ? (
          <div style={{paddingBottom: '12px', color: Colors.Red500, fontSize: '12px'}}>
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

const RecaptchaIFrame: React.FC<{
  newsletter: boolean;
  email: string;
  dismiss: () => void;
}> = ({dismiss, newsletter, email}) => {
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
          ...(iframeLoaded
            ? {}
            : {
                position: 'absolute',
                left: '-99999px',
                width: '304px',
                height: '78px',
              }),
        }}
        onLoad={() => {
          setIframeLoaded(true);
        }}
      />
    </Box>
  );
};

const IFRAME_SRC = '//localhost:4000/dagit_iframes/community_nux';
