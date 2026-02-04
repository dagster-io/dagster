// js_modules/dagster-ui/packages/ui-core/src/runs/RunAlertNotifications.oss.tsx
import {
  Box,
  Button,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  TextInput,
  Tooltip,
} from '@dagster-io/ui-components';
import { useState } from 'react';

import { useMutation } from '../apollo-client';
import { SUBSCRIBE_TO_NOTIFICATIONS_MUTATION } from './RunUtils';
import { validateSubscriptionEmail } from './runNotificationEmail';

export const RunAlertNotifications = (
  {runId, run_subscribers}: 
  {runId: string, run_subscribers: string[]},
) => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [emailInput, setEmailInput] = useState('');
  const [subscribers, setSubscribers] = useState<string[]>(run_subscribers);
  const [validationError, setValidationError] = useState<string | null>(null);

  const [subscribeToNotifications] = useMutation(SUBSCRIBE_TO_NOTIFICATIONS_MUTATION);

  const handleAddEmail = async () => {
    const trimmed = emailInput.trim();
    setValidationError(null);

    const validation = validateSubscriptionEmail(trimmed, subscribers);
    if (!validation.valid) {
      setValidationError(validation.error);
      return;
    }

    const result = await subscribeToNotifications({
      variables: { runId, subscribe: true, email: trimmed },
    });
    const data = result.data?.subscribeToNotifications;
    if (data?.__typename === 'SubscribeToNotificationsSuccess') {
      setSubscribers((prev) => [...prev, trimmed]);
      setEmailInput('');
    } else {
      setValidationError(data?.__typename ? `Error: ${data.__typename}` : 'Failed to subscribe');
    }
  };

  const handleRemoveEmail = async (email: string) => {
    const result = await subscribeToNotifications({
      variables: { runId, subscribe: false, email },
    });
    const data = result.data?.subscribeToNotifications;
    if (data?.__typename === 'SubscribeToNotificationsSuccess') {
      setSubscribers((prev) => prev.filter((e) => e !== email));
    }
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEmailInput('');
    setValidationError(null);
  };

  const handleEmailInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmailInput(e.target.value);
    if (validationError) setValidationError(null);
  };

  return (
    <>
      <Tooltip content="Manage email notifications when this run completes">
        <Button icon={<Icon name="notifications" />} onClick={() => setDialogOpen(true)}>
          Notify on completion
        </Button>
      </Tooltip>
      <Dialog
        isOpen={dialogOpen}
        onClose={handleCloseDialog}
        canOutsideClickClose
        canEscapeKeyClose
        title="Notify when run completes"
        style={{ width: 420 }}
      >
        <DialogBody>
          <Box flex={{ direction: 'column', gap: 16 }}>
            <Box flex={{ direction: 'column', gap: 8 }}>
              <Box flex={{ direction: 'row', gap: 8, alignItems: 'center' }}>
                <TextInput
                  value={emailInput}
                  onChange={handleEmailInputChange}
                  placeholder="Email address"
                  style={{ flex: 1 }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddEmail();
                    }
                  }}
                />
                <Button intent="primary" onClick={handleAddEmail}>
                  Subscribe
                </Button>
              </Box>
              {validationError ? (
                <Box
                  flex={{ direction: 'row', alignItems: 'center', gap: 6 }}
                  style={{ fontSize: 12, color: Colors.accentRed() }}
                >
                  <Icon name="warning" size={12} color={Colors.accentRed()} />
                  {validationError}
                </Box>
              ) : null}
            </Box>
            {subscribers.length > 0 ? (
              <Box flex={{ direction: 'column', gap: 8 }}>
                <div style={{ fontSize: 12, fontWeight: 600 }}>Subscribed emails</div>
                <Box
                  flex={{ direction: 'column', gap: 4 }}
                  style={{ maxHeight: 200, overflow: 'auto' }}
                >
                  {subscribers.map((email) => (
                    <Box
                      key={email}
                      flex={{
                        direction: 'row',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: 8,
                      }}
                      padding={{ vertical: 8, horizontal: 8 }}
                      background={Colors.backgroundDefault()}
                      border="all"
                      style={{ borderRadius: 4 }}
                    >
                      <div style={{ fontSize: 13 }}>{email}</div>
                      <Button
                        icon={<Icon name="close" />}
                        onClick={() => handleRemoveEmail(email)}
                        title="Remove"
                      />
                    </Box>
                  ))}
                </Box>
              </Box>
            ) : null}
          </Box>
        </DialogBody>
        <DialogFooter topBorder>
          <Button onClick={handleCloseDialog}>Close</Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};
