import {Button, Icon, Menu, MenuItem, Popover} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';

import {AutomationInfo, AutomationStateChangeDialog} from './AutomationStateChangeDialog';
import {instigationStateSummary} from '../instigation/instigationStateSummary';
import {OpenWithIntent} from '../instigation/useInstigationStateReducer';

interface Props {
  automations: AutomationInfo[];
}

export const AutomationBulkActionMenu = (props: Props) => {
  const {automations} = props;
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
              text={`启动 ${count === 1 ? '1 个自动化' : `${count} 个自动化`}`}
              disabled={!anyOff}
              aria-disabled={!anyOff}
              icon="toggle_on"
              onClick={() => {
                setOpenWithIntent('start');
              }}
            />
            <MenuItem
              text={`停止 ${count === 1 ? '1 个自动化' : `${count} 个自动化`}`}
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
          操作
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
