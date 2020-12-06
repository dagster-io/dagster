import {gql} from '@apollo/client';
import {Intent, Tag} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showCustomAlert} from 'src/CustomAlertProvider';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {assertUnreachable} from 'src/Util';
import {TickTagFragment} from 'src/types/TickTagFragment';
import {JobTickStatus, JobType} from 'src/types/globalTypes';

export const TickTag: React.FunctionComponent<{
  tick: TickTagFragment;
  jobType: JobType;
}> = ({tick, jobType}) => {
  switch (tick.status) {
    case JobTickStatus.STARTED:
      return (
        <Tag minimal={true} intent={Intent.PRIMARY}>
          Started
        </Tag>
      );
    case JobTickStatus.SUCCESS:
      if (!tick.runs.length) {
        return (
          <Tag minimal={true} intent={Intent.SUCCESS}>
            Success
          </Tag>
        );
      } else {
        // do something smarter here
        // https://github.com/dagster-io/dagster/issues/3352
        const run = tick.runs[0];
        return (
          <a href={`/instance/runs/${run.runId}`} style={{textDecoration: 'none'}}>
            <Tag minimal={true} intent={Intent.SUCCESS} interactive={true}>
              Success
            </Tag>
          </a>
        );
      }
    case JobTickStatus.SKIPPED:
      return (
        <Tag minimal={true} intent={Intent.WARNING}>
          Skipped
        </Tag>
      );
    case JobTickStatus.FAILURE:
      if (!tick.error) {
        return (
          <Tag minimal={true} intent={Intent.DANGER}>
            Failure
          </Tag>
        );
      } else {
        const error = tick.error;
        return (
          <LinkButton
            onClick={() =>
              showCustomAlert({
                title: jobType === JobType.SCHEDULE ? 'Schedule Response' : 'Sensor Response',
                body: <PythonErrorInfo error={error} />,
              })
            }
          >
            <Tag minimal={true} intent={Intent.DANGER} interactive={true}>
              Failure
            </Tag>
          </LinkButton>
        );
      }
    default:
      return assertUnreachable(tick.status);
  }
};

const LinkButton = styled.button`
  background: inherit;
  border: none;
  cursor: pointer;
  font-size: inherit;
  text-decoration: none;
  padding: 0;
`;

export const TICK_TAG_FRAGMENT = gql`
  fragment TickTagFragment on JobTick {
    id
    status
    timestamp
    runs {
      id
      runId
      status
    }
    error {
      ...PythonErrorFragment
    }
  }
`;
