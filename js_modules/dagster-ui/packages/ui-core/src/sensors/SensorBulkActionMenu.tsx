import {Button, Icon, Menu, MenuItem, Popover} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';

import {SensorInfo, SensorStateChangeDialog} from './SensorStateChangeDialog';
import {instigationStateSummary} from '../instigation/instigationStateSummary';
import {OpenWithIntent} from '../instigation/useInstigationStateReducer';

interface Props {
  sensors: SensorInfo[];
  onDone: () => void;
}

export const SensorBulkActionMenu = (props: Props) => {
  const {sensors, onDone} = props;
  const count = sensors.length;

  const [openWithIntent, setOpenWithIntent] = useState<OpenWithIntent>('not-open');

  const {anyOff, anyOn} = useMemo(() => {
    return instigationStateSummary(sensors.map(({sensorState}) => sensorState));
  }, [sensors]);

  return (
    <>
      <Popover
        content={
          <Menu>
            <MenuItem
              text={`Start ${count === 1 ? '1 sensor' : `${count} sensors`}`}
              disabled={!anyOff}
              aria-disabled={!anyOff}
              icon="toggle_on"
              onClick={() => {
                setOpenWithIntent('start');
              }}
            />
            <MenuItem
              text={`Stop ${count === 1 ? '1 sensor' : `${count} sensors`}`}
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
      <SensorStateChangeDialog
        openWithIntent={openWithIntent}
        sensors={sensors}
        onClose={() => setOpenWithIntent('not-open')}
        onComplete={() => {
          onDone();
        }}
      />
    </>
  );
};
