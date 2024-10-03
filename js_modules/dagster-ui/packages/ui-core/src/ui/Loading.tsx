import {Box, NonIdealState, Spinner} from '@dagster-io/ui-components';
import * as React from 'react';

import {ApolloError, QueryResult} from '../apollo-client';
import {ERROR_CODES_TO_SURFACE, errorCodeToMessage} from '../app/HTTPErrorCodes';

interface ILoadingProps<TData> {
  queryResult: Pick<QueryResult<TData, any>, 'error' | 'data' | 'loading'>;
  children: (data: TData) => React.ReactNode;
  renderError?: (error: ApolloError) => React.ReactNode;
  allowStaleData?: boolean;
  purpose?: 'section' | 'page';
}

const BLANK_LOADING_DELAY_MSEC = 500;

export const Loading = <TData extends Record<string, any>>(props: ILoadingProps<TData>) => {
  const {children, purpose = 'page', allowStaleData = false, renderError} = props;
  const {error, data, loading} = props.queryResult;

  const [blankLoading, setBlankLoading] = React.useState(true);
  const isLoading = !data || (loading && !allowStaleData) || Object.keys(data as any).length === 0;

  React.useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;

    // Wait a brief moment so that we don't awkwardly flash the loading bar.
    // This is often enough time for data to become available.
    if (isLoading) {
      timer = setTimeout(() => setBlankLoading(false), BLANK_LOADING_DELAY_MSEC);
    } else {
      setBlankLoading(true);
    }

    return () => {
      timer && clearTimeout(timer);
    };
  }, [isLoading]);

  // either error.networkError or error.graphQLErrors is set,
  // so check that the error is not just a transient network error
  if (error) {
    if (renderError) {
      return <>{renderError(error)}</>;
    }

    const {networkError} = error;
    if (!networkError) {
      return (
        <Box padding={64} flex={{justifyContent: 'center'}}>
          <NonIdealState icon="error" title="GraphQL Error - see console for details" />
        </Box>
      );
    }

    if ('statusCode' in networkError && ERROR_CODES_TO_SURFACE.has(networkError.statusCode)) {
      const statusCode = networkError.statusCode;
      return (
        <Box padding={64} flex={{justifyContent: 'center'}}>
          <NonIdealState
            icon="error"
            title="Network error"
            description={errorCodeToMessage(statusCode)}
          />
        </Box>
      );
    }
  }

  if (isLoading) {
    return blankLoading ? null : <LoadingSpinner purpose={purpose} />;
  }

  return <>{children(data as TData)}</>;
};

export const LoadingSpinner = ({purpose = 'page'}: {purpose?: 'page' | 'section'}) => {
  const isPage = purpose === 'page';
  return (
    <Box
      padding={64}
      flex={{
        grow: isPage ? 1 : undefined,
        justifyContent: 'center',
        alignItems: 'center',
      }}
      style={isPage ? {height: '100%'} : undefined}
    >
      <Spinner purpose={purpose} />
    </Box>
  );
};
