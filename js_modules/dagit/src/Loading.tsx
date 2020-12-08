import {QueryResult} from '@apollo/client';
import {NonIdealState, ProgressBar} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

interface ILoadingProps<TData> {
  queryResult: QueryResult<TData, any>;
  children: (data: TData) => React.ReactNode;
  allowStaleData?: boolean;
}

const BLANK_LOADING_DELAY_MSEC = 500;

export const Loading = <TData extends Record<string, any>>(props: ILoadingProps<TData>) => {
  const {children, allowStaleData = false} = props;
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

  if (error) {
    console.error(error);
    return (
      <LoadingContainer>
        <LoadingCentering>
          <NonIdealState icon={IconNames.ERROR} title="GraphQL Error - see console for details" />
        </LoadingCentering>
      </LoadingContainer>
    );
  }

  if (!data || (loading && !allowStaleData) || Object.keys(data as any).length === 0) {
    return blankLoading ? null : <LoadingWithProgress />;
  }

  return <>{children(data as TData)}</>;
};

export const LoadingWithProgress = () => (
  <LoadingContainer>
    <LoadingCentering>
      <ProgressBar />
    </LoadingCentering>
  </LoadingContainer>
);

const LoadingContainer = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const LoadingCentering = styled.div`
  max-width: 600px;
  width: 75%;
`;
