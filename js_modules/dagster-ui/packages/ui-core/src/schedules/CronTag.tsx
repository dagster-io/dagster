import {Tag, Tooltip} from '@dagster-io/ui-components';
import styled from 'styled-components';

import {humanCronString} from './humanCronString';

interface Props {
  cronSchedule: string;
  executionTimezone: string | null;
}

export const CronTag = (props: Props) => {
  const {cronSchedule, executionTimezone} = props;
  const humanString = humanCronString(cronSchedule, executionTimezone || 'UTC');

  return (
    <Container>
      <Tooltip content={cronSchedule} placement="top">
        <Tag icon="schedule">{humanString}</Tag>
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
