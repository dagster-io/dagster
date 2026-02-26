// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type TickLogEventsQueryVariables = Types.Exact<{
  instigationSelector: Types.InstigationSelector;
  tickId: Types.Scalars['ID']['input'];
}>;

export type TickLogEventsQuery = {
  __typename: 'Query';
  instigationStateOrError:
    | {
        __typename: 'InstigationState';
        id: string;
        instigationType: Types.InstigationType;
        tick: {
          __typename: 'InstigationTick';
          id: string;
          status: Types.InstigationTickStatus;
          timestamp: number;
          logEvents: {
            __typename: 'InstigationEventConnection';
            events: Array<{
              __typename: 'InstigationEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
            }>;
          };
        };
      }
    | {__typename: 'InstigationStateNotFoundError'}
    | {__typename: 'PythonError'};
};

export const TickLogEventsQueryVersion = 'e6e452761c00d82340de471719ccb736472fab2d8d9c0a50c788f78133a6d8b3';
