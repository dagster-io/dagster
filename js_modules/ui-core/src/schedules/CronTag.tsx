import {CaptionMono, MetadataTable, Tag, Tooltip} from '@dagster-io/ui-components';
import {useContext} from 'react';
import styled from 'styled-components';

import {hourOffsetFromUTC} from './hourOffsetFromUTC';
import {humanCronString} from './humanCronString';
import {TimeContext} from '../app/time/TimeContext';

interface Props {
  cronSchedule: string;
  executionTimezone: string | null;
}

export const CronTag = (props: Props) => {
  const {cronSchedule, executionTimezone} = props;
  const {withHumanTimezone, withExecutionTimezone} = useCronInformation(
    cronSchedule,
    executionTimezone,
  );

  const tooltipContent = (
    <MetadataTable
      rows={[
        {key: 'Cron value', value: <CaptionMono>{cronSchedule}</CaptionMono>},
        {key: 'Your time', value: <span>{withHumanTimezone}</span>},
      ]}
    />
  );

  return (
    <Container>
      <Tooltip content={tooltipContent} placement="top">
        <Tag icon="schedule">{withExecutionTimezone}</Tag>
      </Tooltip>
    </Container>
  );
};

export const useCronInformation = (
  cronSchedule: string | null,
  executionTimezone: string | null,
) => {
  const {resolvedTimezone} = useContext(TimeContext);

  if (!cronSchedule) {
    return {
      withHumanTimezone: null,
      withExecutionTimezone: null,
    };
  }

  const longTimezoneName = executionTimezone || 'UTC';
  const humanStringWithExecutionTimezone = humanCronString(cronSchedule, {longTimezoneName});
  const userTimezone = resolvedTimezone;

  const userTimezoneOffset = hourOffsetFromUTC(userTimezone);
  const executionTimezoneOffset = hourOffsetFromUTC(longTimezoneName);
  const tzOffset = userTimezoneOffset - executionTimezoneOffset;

  const humanStringWithUserTimezone = humanCronString(cronSchedule, {
    longTimezoneName: userTimezone,
    tzOffset,
  });

  return {
    withHumanTimezone: humanStringWithUserTimezone,
    withExecutionTimezone: humanStringWithExecutionTimezone,
  };
};

const Container = styled.div`
  .bp5-popover-target {
    max-width: 100%;

    :focus {
      outline: none;
    }
  }
`;
