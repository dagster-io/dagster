import memoize from 'lodash/memoize';
import uniq from 'lodash/uniq';

import {DagsterEventType} from '../graphql/types';

const typeValues = memoize(() =>
  uniq(
    Object.values(DagsterEventType)
      .filter(
        (t) =>
          ![
            DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED,
            DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
          ].includes(t),
      )
      .map(eventTypeToDisplayType),
  ).sort(),
);

export const eventTypeToDisplayType = (eventType: string) => {
  switch (eventType) {
    case DagsterEventType.PIPELINE_STARTING:
      return DagsterEventType.RUN_STARTING;
    case DagsterEventType.PIPELINE_ENQUEUED:
      return DagsterEventType.RUN_ENQUEUED;
    case DagsterEventType.PIPELINE_DEQUEUED:
      return DagsterEventType.RUN_DEQUEUED;
    case DagsterEventType.PIPELINE_STARTING:
      return DagsterEventType.RUN_STARTING;
    case DagsterEventType.PIPELINE_START:
      return DagsterEventType.RUN_START;
    case DagsterEventType.PIPELINE_SUCCESS:
      return DagsterEventType.RUN_SUCCESS;
    case DagsterEventType.PIPELINE_FAILURE:
      return DagsterEventType.RUN_FAILURE;
    case DagsterEventType.PIPELINE_CANCELING:
      return DagsterEventType.RUN_CANCELING;
    case DagsterEventType.PIPELINE_CANCELED:
      return DagsterEventType.RUN_CANCELED;
    case DagsterEventType.PIPELINE_SUCCESS_WITH_WARNINGS:
      return DagsterEventType.RUN_SUCCESS_WITH_WARNINGS;

    default:
      return eventType;
  }
};

export const getRunFilterProviders = memoize(
  (stepNames: string[] = []) => {
    return [
      {
        token: 'step',
        values: () => stepNames,
      },
      {
        token: 'type',
        values: typeValues,
      },
      {
        token: 'query',
        values: () => [],
      },
    ];
  },
  (stepNames: string[] = []) => JSON.stringify(stepNames),
);
