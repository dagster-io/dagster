import {Button, Icon, Menu, MenuItem, Popover} from '@dagster-io/ui-components';
import {useState} from 'react';

import {AutomationInfo, AutomationStateChangeDialog} from './AutomationStateChangeDialog';
import {OpenWithIntent} from '../instigation/useInstigationStateReducer';

interface Props {
  automations: AutomationInfo[];
}

export const AutomationBulkActionMenu = (props: Props) => {
  const {automations} = props;
  const count = automations.length;

  const [openWithIntent, setOpenWithIntent] = useState<OpenWithIntent>('not-open');

  return (
    <>
      <Popover
        content={
          <Menu>
            <MenuItem
              text={`Start ${count === 1 ? '1 automation' : `${count} automations`}`}
              icon="toggle_on"
              onClick={() => {
                setOpenWithIntent('start');
              }}
            />
            <MenuItem
              text={`Stop ${count === 1 ? '1 automation' : `${count} automations`}`}
              icon="toggle_off"
              onClick={() => {
                setOpenWithIntent('stop');
              }}
            />
          </Menu>
        }
        placement="bottom-end"
      >
        <Button disabled={!count} intent="primary" rightIcon={<Icon name="expand_more" />}>
          Actions
        </Button>
      </Popover>
      <AutomationStateChangeDialog
        openWithIntent={openWithIntent}
        automations={automations}
        onClose={() => setOpenWithIntent('not-open')}
      />
    </>
  );
};
