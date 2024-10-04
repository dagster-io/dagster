import {Box, Heading} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

export const CodeLocationPageHeaderTitle = ({repoAddress}: {repoAddress: RepoAddress}) => {
  return (
    <Heading>
      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
        <div>
          <Link to="/deployment/locations">Code locations</Link>
        </div>
        <div>/</div>
        <div>{repoAddressAsHumanString(repoAddress)}</div>
      </Box>
    </Heading>
  );
};
