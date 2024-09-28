import {Button, Icon, Menu, MenuItem, Popover} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';

import {AutomationInfo, AutomationStateChangeDialog} from './AutomationStateChangeDialog';
import {instigationStateSummary} from '../instigation/instigationStateSummary';
import {OpenWithIntent} from '../instigation/useInstigationStateReducer';

interface Props {
  automations: AutomationInfo[];
  onDone: () => void;
}

export const AutomationBulkActionMenu = (props: Props) => {
  const {automations, onDone} = props;
  const count = automations.length;

  const [openWithIntent, setOpenWithIntent] = useState<OpenWithIntent>('not-open');

  const {anyOff, anyOn} = useMemo(() => {
    return instigationStateSummary(automations.map(({instigationState}) => instigationState));
  }, [automations]);

  return (
    <>
      <Popover
        content={
          <Menu>
            <MenuItem
              text={`Start ${count === 1 ? '1 automation' : `${count} automations`}`}
              disabled={!anyOff}
              aria-disabled={!anyOff}
              icon="toggle_on"
              onClick={() => {
                setOpenWithIntent('start');
              }}
            />
            <MenuItem
              text={`Stop ${count === 1 ? '1 automation' : `${count} automations`}`}
              disabled={!anyOn}
              aria-disabled={!anyOn}
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
        onComplete={() => {
          onDone();
        }}
      />
    </>
  );
};
