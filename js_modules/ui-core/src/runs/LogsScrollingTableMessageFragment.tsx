import {LOGS_ROW_STRUCTURED_FRAGMENT, LOGS_ROW_UNSTRUCTURED_FRAGMENT} from './LogsRow';
import {gql} from '../apollo-client';

export const LOGS_SCROLLING_TABLE_MESSAGE_FRAGMENT = gql`
  fragment LogsScrollingTableMessageFragment on DagsterRunEvent {
    ...LogsRowStructuredFragment
    ...LogsRowUnstructuredFragment
  }

  ${LOGS_ROW_STRUCTURED_FRAGMENT}
  ${LOGS_ROW_UNSTRUCTURED_FRAGMENT}
`;
