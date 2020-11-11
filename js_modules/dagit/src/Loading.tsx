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

export const Loading = <TData extends Record<string, any>>(props: ILoadingProps<TData>) => {
  const {children, allowStaleData = false} = props;
  const {error, data, loading} = props.queryResult;

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
  if (!data || (loading && !allowStaleData) || Object.keys(data).length === 0) {
    return <LoadingWithProgress />;
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

export const LoadingContainer = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
`;

export const LoadingCentering = styled.div`
  max-width: 600px;
  width: 75%;
`;
