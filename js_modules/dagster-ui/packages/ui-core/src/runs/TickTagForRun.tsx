import {Box, ButtonLink, MiddleTruncate, Tag} from '@dagster-io/ui-components';
import {useState} from 'react';

import {DagsterTag} from './RunTag';
import {InstigationSelector} from '../graphql/types';
import {TickDetailsDialog} from '../instigation/TickDetailsDialog';

interface Props {
  instigationSelector: InstigationSelector;
  instigationType: DagsterTag.SensorName | DagsterTag.ScheduleName;
  tickId: string;
}

export const TickTagForRun = ({instigationSelector, instigationType, tickId}: Props) => {
  const [isOpen, setIsOpen] = useState(false);
  const icon = instigationType === DagsterTag.ScheduleName ? 'schedule' : 'sensors';
  const {name} = instigationSelector;

  return (
    <>
      <Tag icon={icon}>
        <Box flex={{direction: 'row'}}>
          <span>Launched by&nbsp;</span>
          <ButtonLink onClick={() => setIsOpen(true)}>
            <div style={{maxWidth: '140px'}}>
              <MiddleTruncate text={name} />
            </div>
          </ButtonLink>
        </Box>
      </Tag>
      <TickDetailsDialog
        isOpen={isOpen}
        tickResultType="runs"
        onClose={() => setIsOpen(false)}
        instigationSelector={instigationSelector}
        tickId={tickId}
      />
    </>
  );
};
