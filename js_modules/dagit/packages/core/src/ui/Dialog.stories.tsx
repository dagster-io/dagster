import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {ButtonWIP} from './Button';
import {
  DialogBody,
  DialogButtons,
  DialogFooter,
  DialogHeader,
  DialogWIP as Dialog,
  DialogWIP,
  GlobalDialogStyle,
} from './Dialog';
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
      <ButtonWIP onClick={() => setOpen(true)}>Show me the dialog</ButtonWIP>
      <DialogWIP
        isOpen={open}
        canEscapeKeyClose
        canOutsideClickClose
        onClose={() => setOpen(false)}
      >
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
        <DialogFooter
          right={
            <DialogButtons>
              <ButtonWIP intent="none" onClick={() => setOpen(false)}>
                Cancel
              </ButtonWIP>
              <ButtonWIP intent="primary" onClick={() => setOpen(false)}>
                Perform action
              </ButtonWIP>
            </DialogButtons>
          }
        />
      </DialogWIP>
    </>
  );
};
