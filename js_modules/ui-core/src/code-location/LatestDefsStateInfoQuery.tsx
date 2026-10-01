import {gql} from '../apollo-client';
import {DEFS_STATE_INFO_FRAGMENT} from './CodeLocationDefsStateQuery';

// Lightweight read from defs_state_storage — used by the refresh button to
// poll for version bumps without paying the cost of refetching the full
// components list. Workspace-scoped: ``latestDefsStateInfo`` covers every
// location, so the caller filters by ``defsStateKey``.
export const LATEST_DEFS_STATE_INFO_QUERY = gql`
  query LatestDefsStateInfoQuery {
    latestDefsStateInfo {
      ...DefsStateInfoFragment
    }
  }
  ${DEFS_STATE_INFO_FRAGMENT}
`;
