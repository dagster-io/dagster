import {CaptionMono, MetadataTable, Tag, Tooltip} from '@dagster-io/ui-components';
import {useContext} from 'react';
import styled from 'styled-components';

import {hourOffsetFromUTC} from './hourOffsetFromUTC';
import {humanCronString} from './humanCronString';
import {TimeContext} from '../app/time/TimeContext';
import {browserTimezone} from '../app/time/browserTimezone';

interface Props {
  cronSchedule: string;
  executionTimezone: string | null;
}

export const CronTag = (props: Props) => {
  const {cronSchedule, executionTimezone} = props;
  const {
    timezone: [storedTimezone],
  } = useContext(TimeContext);

  const longTimezoneName = executionTimezone || 'UTC';
  const humanStringWithExecutionTimezone = humanCronString(cronSchedule, {longTimezoneName});
  const userTimezone = storedTimezone === 'Automatic' ? browserTimezone() : storedTimezone;

  const userTimezoneOffset = hourOffsetFromUTC(userTimezone);
  const executionTimezoneOffset = hourOffsetFromUTC(longTimezoneName);
  const tzOffset = userTimezoneOffset - executionTimezoneOffset;

  const humanStringWithUserTimezone = humanCronString(cronSchedule, {
    longTimezoneName: userTimezone,
    tzOffset,
  });

  const tooltipContent = (
    <MetadataTable
      rows={[
        {key: 'Cron value', value: <CaptionMono>{cronSchedule}</CaptionMono>},
        {key: 'Your time', value: <span>{humanStringWithUserTimezone}</span>},
      ]}
    />
  );

  return (
    <Container>
      <Tooltip content={tooltipContent} placement="top">
        <Tag icon="schedule">{humanStringWithExecutionTimezone}</Tag>
      </Tooltip>
    </Container>
  );
};

const Container = styled.div`
  .bp5-popover-target {
    max-width: 100%;

    :focus {
      outline: none;
    }
  }
`;
