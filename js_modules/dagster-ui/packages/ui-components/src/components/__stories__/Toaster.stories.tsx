// eslint-disable-next-line no-restricted-imports
import {Intent} from '@blueprintjs/core';
import {Meta} from '@storybook/react';
import {useEffect, useRef} from 'react';

import {Button} from '../Button';
import {Group} from '../Group';
import {DToaster, DToasterShowProps, GlobalToasterStyle, Toaster} from '../Toaster';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Toaster',
} as Meta;

export const Sizes = () => {
  const sharedToaster = useRef<DToaster | null>(null);

  useEffect(() => {
    const makeToaster = async () => {
      sharedToaster.current = await Toaster.asyncCreate({position: 'top'}, document.body);
    };
    makeToaster();
  }, []);

  const showSharedToaster = async (config: DToasterShowProps) => {
    if (sharedToaster.current) {
      sharedToaster.current.show(config);
    }
  };

  return (
    <Group direction="column" spacing={16}>
      <GlobalToasterStyle />

      <Button
        onClick={async () =>
          await showSharedToaster({
            intent: Intent.NONE,
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
          await showSharedToaster({
            intent: Intent.SUCCESS,
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
          await showSharedToaster({
            intent: Intent.DANGER,
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
          await showSharedToaster({
            intent: Intent.PRIMARY,
            timeout: 5000,
            message: 'This is a primary toaster',
            icon: 'account_circle',
          })
        }
      >
        Primary Toast
      </Button>
    </Group>
  );
};
