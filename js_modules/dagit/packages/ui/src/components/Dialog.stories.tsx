import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Button} from './Button';
import {DialogBody, DialogFooter, DialogHeader, Dialog, GlobalDialogStyle} from './Dialog';
import {Group} from './Group';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Dialog',
  component: Dialog,
} as Meta;

export const Simple = () => {
  const [open, setOpen] = React.useState(false);
  return (
    <>
      <GlobalDialogStyle />
      <Button onClick={() => setOpen(true)}>Show me the dialog</Button>
      <Dialog isOpen={open} canEscapeKeyClose canOutsideClickClose onClose={() => setOpen(false)}>
        <DialogHeader icon="layers" label="Start the process" />
        <DialogBody>
          <Group direction="column" spacing={12}>
            <div>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
              incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
              exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
            </div>
            <div>
              Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat
              nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui
              officia deserunt mollit anim id est laborum.
            </div>
          </Group>
        </DialogBody>
        <DialogFooter>
          <Button intent="none" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button intent="primary" onClick={() => setOpen(false)}>
            Perform action
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};
