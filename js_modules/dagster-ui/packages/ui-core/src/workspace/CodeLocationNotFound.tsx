import {Box, NonIdealState} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {repoAddressAsHumanString} from './repoAddressAsString';
import {RepoAddress} from './types';

export const CodeLocationNotFound = ({repoAddress}: {repoAddress: RepoAddress}) => {
  const displayName = repoAddressAsHumanString(repoAddress);
  return (
    <NonIdealState
      icon="code_location"
      title="Code location not found"
      description={
        <Box flex={{direction: 'column', gap: 12}} style={{wordBreak: 'break-word'}}>
          <div>
            Code location <strong>{displayName}</strong> is not available in this workspace.
          </div>
          <div>
            Check your <Link to="/deployment">deployment settings</Link> for errors.
          </div>
        </Box>
      }
    />
  );
};
