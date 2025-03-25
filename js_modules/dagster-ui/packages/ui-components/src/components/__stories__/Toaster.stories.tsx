// eslint-disable-next-line no-restricted-imports
import {Meta} from '@storybook/react';

import {Button} from '../Button';
import {Group} from '../Group';
import {showToast} from '../Toaster';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Toaster',
} as Meta;

export const Sizes = () => {
  return (
    <Group direction="column" spacing={16}>
      <Button
        onClick={async () =>
          await showToast({
            intent: 'none',
            message: 'Code location reloaded',
            timeout: 300000,
            icon: 'done',
          })
        }
      >
        Basic Toast with Icon
      </Button>
      <Button
        onClick={async () =>
          await showToast({
            intent: 'success',
            timeout: 300000,
            message: (
              <div>
                Created backfill job:{' '}
                <strong>
                  <code>12345</code>
                </strong>
              </div>
            ),
          })
        }
      >
        Success Toast with React Content
      </Button>
      <Button
        onClick={async () =>
          await showToast({
            intent: 'danger',
            timeout: 300000,
            message: 'This is an error message',
            icon: 'error',
          })
        }
      >
        Error Toast
      </Button>
      <Button
        onClick={async () =>
          await showToast({
            intent: 'primary',
            timeout: 5000,
            message: 'This is a primary toaster',
            icon: 'account_circle',
          })
        }
      >
        Primary Toast
      </Button>
      <Button
        onClick={async () =>
          await showToast({
            intent: 'danger',
            message: 'Oh no an error! Look at the console!',
            timeout: 300000,
            action: {
              type: 'button',
              text: 'View error',
              onClick: () => {
                console.log('HERE IS AN ERROR IN THE CONSOLE');
              },
            },
          })
        }
      >
        Toast with Action
      </Button>
    </Group>
  );
};
