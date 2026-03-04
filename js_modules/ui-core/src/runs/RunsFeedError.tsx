import {Box, NonIdealState} from '@dagster-io/ui-components';

import {ApolloError} from '../apollo-client';

export const RunsFeedError = ({error}: {error: ApolloError | undefined}) => {
  const badRequest = !!(
    typeof error === 'object' &&
    'statusCode' in error &&
    error.statusCode === 400
  );
  return (
    <Box flex={{direction: 'column', gap: 32}} padding={{vertical: 8}} border="top">
      <NonIdealState
        icon="warning"
        title={badRequest ? 'Invalid run filters' : 'Unexpected error'}
        description={
          badRequest
            ? 'The specified run filters are not valid. Please check the filters and try again.'
            : 'An unexpected error occurred. Check the console for details.'
        }
      />
    </Box>
  );
};
