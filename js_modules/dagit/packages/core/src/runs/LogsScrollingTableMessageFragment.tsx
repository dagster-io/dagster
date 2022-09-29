import {gql} from '@apollo/client';

import {LOGS_ROW_STRUCTURED_FRAGMENT} from './LogsRowStructuredFragment';
import {LOGS_ROW_UNSTRUCTURED_FRAGMENT} from './LogsRowUnstructuredFragment';

export const LOGS_SCROLLING_TABLE_MESSAGE_FRAGMENT = gql`
  fragment LogsScrollingTableMessageFragment on DagsterRunEvent {
    __typename
    ...LogsRowStructuredFragment
    ...LogsRowUnstructuredFragment
  }

  ${LOGS_ROW_STRUCTURED_FRAGMENT}
  ${LOGS_ROW_UNSTRUCTURED_FRAGMENT}
`;
