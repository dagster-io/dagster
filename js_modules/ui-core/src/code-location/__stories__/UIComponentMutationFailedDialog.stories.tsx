import {UIComponentMutationFailedDialog} from '../UIComponentMutationFailedDialog';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'CodeLocation/UIComponentMutationFailedDialog',
  component: UIComponentMutationFailedDialog,
};

const ERROR_MESSAGE =
  'Traceback (most recent call last):\n' +
  '  File "definitions.py", line 42, in load\n' +
  "    raise ValueError('component value out of range: 9999')\n" +
  'ValueError: component value out of range: 9999';

export const AddFailed = () => (
  <UIComponentMutationFailedDialog
    isOpen={true}
    ctx={{
      kind: 'add',
      componentId: 'my_component[1]',
      componentType: 'dagster.MyComponent',
    }}
    errorMessage={ERROR_MESSAGE}
    isReverting={false}
    onRevert={() => {}}
    onDismiss={() => {}}
  />
);

export const EditFailed = () => (
  <UIComponentMutationFailedDialog
    isOpen={true}
    ctx={{
      kind: 'edit',
      componentId: 'my_component[1]',
      componentType: 'dagster.MyComponent',
      prevAttributes: 'config:\n  value: 7\n',
    }}
    errorMessage={ERROR_MESSAGE}
    isReverting={false}
    onRevert={() => {}}
    onDismiss={() => {}}
  />
);

export const DeleteFailed = () => (
  <UIComponentMutationFailedDialog
    isOpen={true}
    ctx={{
      kind: 'delete',
      componentId: 'my_component[1]',
      componentType: 'dagster.MyComponent',
      prevAttributes: 'config:\n  value: 7\n',
    }}
    errorMessage={ERROR_MESSAGE}
    isReverting={false}
    onRevert={() => {}}
    onDismiss={() => {}}
  />
);

export const Reverting = () => (
  <UIComponentMutationFailedDialog
    isOpen={true}
    ctx={{
      kind: 'edit',
      componentId: 'my_component[1]',
      componentType: 'dagster.MyComponent',
      prevAttributes: 'config:\n  value: 7\n',
    }}
    errorMessage={ERROR_MESSAGE}
    isReverting={true}
    onRevert={() => {}}
    onDismiss={() => {}}
  />
);

export const NoContext = () => (
  <UIComponentMutationFailedDialog
    isOpen={true}
    ctx={null}
    errorMessage={ERROR_MESSAGE}
    isReverting={false}
    onRevert={() => {}}
    onDismiss={() => {}}
  />
);
