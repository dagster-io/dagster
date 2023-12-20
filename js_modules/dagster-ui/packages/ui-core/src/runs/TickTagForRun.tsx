import {ButtonLink, MiddleTruncate, Tag} from '@dagster-io/ui-components';
import * as React from 'react';

import {InstigationSelector} from '../graphql/types';
import {TickDetailsDialog} from '../instigation/TickDetailsDialog';

import {DagsterTag} from './RunTag';

interface Props {
  instigationSelector: InstigationSelector;
  instigationType: DagsterTag.SensorName | DagsterTag.ScheduleName;
  tickId: string;
}

export const TickTagForRun = ({instigationSelector, instigationType, tickId}: Props) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const icon = instigationType === DagsterTag.ScheduleName ? 'schedule' : 'sensors';
  const {name} = instigationSelector;

  return (
    <>
      <Tag icon={icon}>
        <span>
          Launched by{' '}
          <ButtonLink onClick={() => setIsOpen(true)}>
            <div style={{maxWidth: '140px'}}>
              <MiddleTruncate text={name} />
            </div>
          </ButtonLink>
        </span>
      </Tag>
      <TickDetailsDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        instigationSelector={instigationSelector}
        tickId={Number(tickId)}
      />
    </>
  );
};
