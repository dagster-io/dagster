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

const CommunityNuxImpl: React.FC<{dismiss: () => void}> = ({dismiss}) => {
  const [shouldShowNux, setShouldShowNux] = React.useState(false);
  React.useEffect(() => {
    const timeout = setTimeout(() => {
      setShouldShowNux(true);
    }, 5000); // wait 5 seconds before showing Nux
    return () => {
      clearTimeout(timeout);
    };
  }, []);

  const [email, setEmail] = React.useState('');
  const [newsletter, setNewsLetter] = React.useState(false);

  const submit = async () => {
    await fetch('http://dagster.cloud/email-sign-up', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        newsletter,
      }),
    });
    dismiss();
  };

  const validEmail = isEmail(email);
  const [emailChanged, setEmailChanged] = React.useState(false);

  return (
    <Dialog isOpen={shouldShowNux} style={{width: '680px'}}>
      <Box flex={{direction: 'column', gap: 16}} style={{padding: '36px'}}>
        <Box
          flex={{direction: 'row', gap: 24, alignItems: 'center'}}
          padding={{bottom: 24}}
          border={{side: 'bottom', color: Colors.KeylineGray, width: 1}}
        >
          <Box flex={{direction: 'column', gap: 8}}>
            <Heading>Join the Dagster community</Heading>
            <Body style={{color: Colors.Gray700}}>
              Connect with thousands of other data practitioners building with Dagster. Share
              knowledge, get help, and contribute to the open-source project.
            </Body>
            <div>
              <ExternalAnchorButton
                icon={<Icon name="slack" />}
                href="https://www.dagster.io/slack"
              >
                Join us on Slack
              </ExternalAnchorButton>
            </div>
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
            placeholder="hello@dagster.io"
            strokeColor={!emailChanged || validEmail ? undefined : Colors.Red500}
            style={{width: '100%'}}
          />
          {emailChanged && !validEmail ? (
            <div style={{paddingBottom: '12px', color: Colors.Red500, fontSize: '12px'}}>
              Add your email to get updates from Dagster.
            </div>
          ) : null}
          <Box flex={{direction: 'column', gap: 8}} padding={{bottom: 24}}>
            <Box as="label" flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <Checkbox checked={true} disabled={true} onChange={() => {}} />
              <span>Notify me about Dagster security updates</span>
            </Box>
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
            <Button onClick={submit} disabled={!validEmail} intent="primary">
              Submit
            </Button>
          </Box>
        </Box>
      </Box>
    </Dialog>
  );
};
