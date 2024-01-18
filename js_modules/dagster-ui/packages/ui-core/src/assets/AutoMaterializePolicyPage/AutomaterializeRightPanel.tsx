import * as React from 'react';
import {gql, useQuery} from '@apollo/client';
import {Link, Redirect} from 'react-router-dom';

import {
  Body,
  Box,
  ExternalAnchorButton,
  Icon,
  Mono,
  NonIdealState,
  Spinner,
  Subheading,
} from '@dagster-io/ui-components';

import {ErrorWrapper} from '../../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {AutomaterializePolicyTag} from '../AutomaterializePolicyTag';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';
import {AssetKey} from '../types';
import {
  GetPolicyInfoQuery,
  GetPolicyInfoQueryVariables,
} from './types/AutomaterializeRightPanel.types';

interface Props {
  assetKey: AssetKey;
}

export const AutomaterializeRightPanel = ({assetKey}: Props) => {
  const queryResult = useQuery<GetPolicyInfoQuery, GetPolicyInfoQueryVariables>(
    GET_POLICY_INFO_QUERY,
    {variables: {assetKey}},
  );

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {data, error} = queryResult;

  return (
    <Box flex={{direction: 'column'}} style={{width: '294px', height: '100%'}} border="left">
      <Box padding={16} border="bottom">
        <Subheading>Overview</Subheading>
      </Box>
      <div style={{overflowY: 'auto'}}>
        {error ? (
          <Box padding={24}>
            <ErrorWrapper>{JSON.stringify(error)}</ErrorWrapper>
          </Box>
        ) : !data ? (
          <Box flex={{direction: 'row', justifyContent: 'center'}} padding={{vertical: 24}}>
            <Spinner purpose="section" />
          </Box>
        ) : data.assetNodeOrError.__typename === 'AssetNotFoundError' ? (
          <Redirect to="/assets" />
        ) : (
          <>
            {data.assetNodeOrError.autoMaterializePolicy ? (
              <RightPanelSection
                title={
                  <Box
                    flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
                  >
                    Auto-materialize policy
                    <AutomaterializePolicyTag
                      policy={data.assetNodeOrError.autoMaterializePolicy}
                    />
                  </Box>
                }
              >
                <Body style={{flex: 1}}>
                  This asset will be automatically materialized when at least one of the conditions
                  to the left is met and no skip conditions are met.
                </Body>
              </RightPanelSection>
            ) : (
              <Box padding={8}>
                <NonIdealState
                  title="No auto-materialize policy found"
                  shrinkable
                  description={
                    <Box flex={{direction: 'column', gap: 8}}>
                      <div>
                        An auto-materialize policy specifies how Dagster should attempt to keep an
                        asset up-to-date.
                      </div>
                      <div>
                        <ExternalAnchorButton
                          href="https://docs.dagster.io/_apidocs/assets#dagster.AutoMaterializePolicy"
                          target="_blank"
                          rel="noreferrer"
                          icon={<Icon name="open_in_new" />}
                        >
                          View documentation
                        </ExternalAnchorButton>
                      </div>
                    </Box>
                  }
                />
              </Box>
            )}
            {data.assetNodeOrError.freshnessPolicy ? (
              <RightPanelSection title="Freshness policy">
                <RightPanelDetail
                  title="Maximum lag minutes"
                  value={data.assetNodeOrError.freshnessPolicy.maximumLagMinutes}
                />
                <Box flex={{direction: 'column', gap: 8}}>
                  This asset will be considered late if it is not materialized within{' '}
                  {data.assetNodeOrError.freshnessPolicy.maximumLagMinutes} minutes of it’s upstream
                  dependencies.
                  <Link
                    to={assetDetailsPathForKey(assetKey, {
                      view: 'lineage',
                      lineageScope: 'upstream',
                    })}
                  >
                    View upstream assets
                  </Link>
                </Box>
              </RightPanelSection>
            ) : (
              <Box padding={8}>
                <NonIdealState
                  title="No freshness policy found"
                  shrinkable
                  description={
                    <Box flex={{direction: 'column', gap: 8}}>
                      <div>
                        A FreshnessPolicy specifies how up-to-date you want a given asset to be.
                      </div>
                      <div>
                        <ExternalAnchorButton
                          href="https://docs.dagster.io/_apidocs/assets#dagster.FreshnessPolicy"
                          target="_blank"
                          rel="noreferrer"
                          icon={<Icon name="open_in_new" />}
                        >
                          View documentation
                        </ExternalAnchorButton>
                      </div>
                    </Box>
                  }
                />
              </Box>
            )}
          </>
        )}
      </div>
    </Box>
  );
};

const RightPanelSection = ({
  title,
  children,
}: {
  title: React.ReactNode;
  children: React.ReactNode;
}) => {
  return (
    <Box
      flex={{direction: 'column', gap: 12}}
      border="bottom"
      padding={{vertical: 12, horizontal: 16}}
    >
      <Subheading>{title}</Subheading>
      {children}
    </Box>
  );
};

const RightPanelDetail = ({
  title,
  value,
}: {
  title: React.ReactNode;
  tooltip?: React.ReactNode;
  value: React.ReactNode;
}) => {
  return (
    <Box flex={{direction: 'column', gap: 4}}>
      <div>{title}</div>
      <Mono style={{fontSize: '16px', fontWeight: 500}}>{value}</Mono>
    </Box>
  );
};

export const GET_POLICY_INFO_QUERY = gql`
  query GetPolicyInfoQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        freshnessPolicy {
          maximumLagMinutes
          cronSchedule
          cronScheduleTimezone
        }
        autoMaterializePolicy {
          policyType
          maxMaterializationsPerMinute
          rules {
            description
            decisionType
          }
        }
      }
    }
  }
`;
