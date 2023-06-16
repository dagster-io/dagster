import {gql, useQuery} from '@apollo/client';
import {
  Body,
  Box,
  Colors,
  ExternalAnchorButton,
  Icon,
  NonIdealState,
  Spinner,
  Subheading,
  Tag,
} from '@dagster-io/ui';
import * as React from 'react';
import {Redirect} from 'react-router';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {ErrorWrapper} from '../../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {
  AutomaterializePolicyTag,
  automaterializePolicyDescription,
} from '../AutomaterializePolicyTag';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';
import {AssetKey} from '../types';

import {AutomaterializeLeftPanel} from './AutomaterializeLeftPanel';
import {GET_EVALUATIONS_QUERY} from './GetEvaluationsQuery';
import {getEvaluationsWithEmptyAdded} from './getEvaluationsWithEmptyAdded';
import {NoConditionsMetEvaluation} from './types';
import {
  GetPolicyInfoQuery,
  GetPolicyInfoQueryVariables,
} from './types/AssetAutomaterializePolicyPage.types';
import {
  AutoMaterializeEvaluationRecordItemFragment,
  GetEvaluationsQuery,
  GetEvaluationsQueryVariables,
} from './types/GetEvaluationsQuery.types';
import {useEvaluationsQueryResult} from './useEvaluationsQueryResult';

export const AssetAutomaterializePolicyPage = ({
  assetKey,
  assetHasDefinedPartitions,
}: {
  assetKey: AssetKey;
  assetHasDefinedPartitions: boolean;
}) => {
  const {queryResult, paginationProps} = useEvaluationsQueryResult({assetKey});

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const {evaluations, currentEvaluationId} = React.useMemo(() => {
    if (
      queryResult.data?.autoMaterializeAssetEvaluationsOrError?.__typename ===
      'AutoMaterializeAssetEvaluationRecords'
    ) {
      return {
        evaluations: queryResult.data?.autoMaterializeAssetEvaluationsOrError.records,
        currentEvaluationId:
          queryResult.data.autoMaterializeAssetEvaluationsOrError.currentEvaluationId,
      };
    }
    return {evaluations: [], currentEvaluationId: null};
  }, [queryResult.data?.autoMaterializeAssetEvaluationsOrError]);

  const isFirstPage = !paginationProps.hasPrevCursor;
  const isLastPage = !paginationProps.hasNextCursor;
  const isLoading = queryResult.loading && !queryResult.data;
  const evaluationsIncludingEmpty = React.useMemo(
    () =>
      getEvaluationsWithEmptyAdded({
        currentEvaluationId,
        evaluations,
        isFirstPage,
        isLastPage,
        isLoading,
      }),
    [currentEvaluationId, evaluations, isFirstPage, isLastPage, isLoading],
  );

  const [selectedEvaluationId, setSelectedEvaluationId] = useQueryPersistedState<
    number | undefined
  >({
    queryKey: 'evaluation',
    decode: (raw) => {
      const value = parseInt(raw.evaluation);
      return isNaN(value) ? undefined : value;
    },
  });

  const selectedEvaluation = React.useMemo(() => {
    if (selectedEvaluationId) {
      const found = evaluationsIncludingEmpty.find(
        (evaluation) => evaluation.evaluationId === selectedEvaluationId,
      );
      if (found) {
        return found;
      }
    }
    return evaluationsIncludingEmpty[0];
  }, [selectedEvaluationId, evaluationsIncludingEmpty]);

  const [maxMaterializationsPerMinute, setMaxMaterializationsPerMinute] = React.useState(1);

  return (
    <AutomaterializePage
      style={{flex: 1, minHeight: 0, color: Colors.Gray700}}
      flex={{direction: 'row'}}
    >
      <Box
        flex={{direction: 'column', grow: 1}}
        border={{side: 'right', width: 1, color: Colors.KeylineGray}}
      >
        <CenterAlignedRow
          flex={{justifyContent: 'space-between'}}
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <Subheading>Evaluation history</Subheading>
        </CenterAlignedRow>
        <Box flex={{direction: 'row'}} style={{flex: 1, minHeight: 0}}>
          <Box
            border={{side: 'right', color: Colors.KeylineGray, width: 1}}
            flex={{grow: 0, direction: 'column'}}
            style={{flex: '0 0 296px'}}
          >
            <AutomaterializeLeftPanel
              assetHasDefinedPartitions={assetHasDefinedPartitions}
              evaluations={evaluations}
              evaluationsIncludingEmpty={evaluationsIncludingEmpty}
              paginationProps={paginationProps}
              onSelectEvaluation={(evaluation) => {
                setSelectedEvaluationId(evaluation.evaluationId);
              }}
              selectedEvaluation={selectedEvaluation}
            />
          </Box>
          <Box flex={{grow: 1}} style={{minHeight: 0}}>
            <MiddlePanel
              assetKey={assetKey}
              key={selectedEvaluation?.evaluationId || ''}
              maxMaterializationsPerMinute={maxMaterializationsPerMinute}
              selectedEvaluation={selectedEvaluation}
            />
          </Box>
        </Box>
      </Box>
      <Box>
        <RightPanel
          assetKey={assetKey}
          setMaxMaterializationsPerMinute={setMaxMaterializationsPerMinute}
        />
      </Box>
    </AutomaterializePage>
  );
};

const RightPanel = ({
  assetKey,
  setMaxMaterializationsPerMinute,
}: {
  assetKey: Omit<AssetKey, '__typename'>;
  setMaxMaterializationsPerMinute: (max: number) => void;
}) => {
  const queryResult = useQuery<GetPolicyInfoQuery, GetPolicyInfoQueryVariables>(
    GET_POLICY_INFO_QUERY,
    {
      variables: {
        assetKey,
      },
    },
  );
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {data, error} = queryResult;

  React.useEffect(() => {
    if (data?.assetNodeOrError.__typename === 'AssetNode') {
      const max = data.assetNodeOrError.autoMaterializePolicy?.maxMaterializationsPerMinute;
      if (typeof max === 'number') {
        setMaxMaterializationsPerMinute(max);
      }
    }
  }, [data, setMaxMaterializationsPerMinute]);

  return (
    <Box flex={{direction: 'column'}} style={{width: '294px'}}>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <Subheading>Overview</Subheading>
      </Box>
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
                  <AutomaterializePolicyTag policy={data.assetNodeOrError.autoMaterializePolicy} />
                </Box>
              }
            >
              <Body style={{flex: 1}}>
                {automaterializePolicyDescription(data.assetNodeOrError.autoMaterializePolicy)}
              </Body>
            </RightPanelSection>
          ) : (
            <NonIdealState
              title="No auto-materialize policy found"
              shrinkable
              description={
                <Box flex={{direction: 'column', gap: 8}}>
                  <div>
                    An auto-materialize policy specifies how Dagster should attempt to keep an asset
                    up-to-date.
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
                  to={assetDetailsPathForKey(assetKey, {view: 'lineage', lineageScope: 'upstream'})}
                >
                  View upstream assets
                </Link>
              </Box>
            </RightPanelSection>
          ) : (
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
          )}
        </>
      )}
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
      border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
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
    <Box flex={{direction: 'column', gap: 2}}>
      <CenterAlignedRow flex={{gap: 6}}>{title}</CenterAlignedRow>
      {value}
    </Box>
  );
};

const MiddlePanel = ({
  assetKey,
  selectedEvaluation,
  maxMaterializationsPerMinute,
}: {
  assetKey: Omit<AssetKey, '__typename'>;
  selectedEvaluation?: AutoMaterializeEvaluationRecordItemFragment | NoConditionsMetEvaluation;
  maxMaterializationsPerMinute: number;
}) => {
  const {data, loading, error} = useQuery<GetEvaluationsQuery, GetEvaluationsQueryVariables>(
    GET_EVALUATIONS_QUERY,
    {
      variables: {
        assetKey,
        cursor: selectedEvaluation?.evaluationId
          ? (selectedEvaluation.evaluationId + 1).toString()
          : undefined,
        limit: 2,
      },
    },
  );

  const conditionResults = React.useMemo(() => {
    const results: Partial<{
      materializationIsMissing: boolean;
      codeVersionHasChangedSinceLastMaterialization: boolean;
      upstreamCodeVersionHasChangedSinceLastMaterialization: boolean;
      upstreamDataHasChangedSinceLatestMaterialization: boolean;
      requiredToMeetAFreshnessPolicy: boolean;
      requiredToMeetADownstreamFreshnessPolicy: boolean;

      // skip conditions
      waitingOnUpstreamData: boolean;
      exceedsMaxMaterializationsPerMinute: boolean;
    }> = {};
    selectedEvaluation?.conditions?.forEach((cond: any) => {
      switch (cond.__typename) {
        case 'DownstreamFreshnessAutoMaterializeCondition':
          results.requiredToMeetADownstreamFreshnessPolicy = true;
          break;
        case 'FreshnessAutoMaterializeCondition':
          results.requiredToMeetAFreshnessPolicy = true;
          break;
        case 'MissingAutoMaterializeCondition':
          results.materializationIsMissing = true;
          break;
        case 'ParentMaterializedAutoMaterializeCondition':
          results.upstreamDataHasChangedSinceLatestMaterialization = true;
          break;
        case 'ParentOutdatedAutoMaterializeCondition':
          results.waitingOnUpstreamData = true;
          break;
        case 'MaxMaterializationsExceededAutoMaterializeCondition':
          results.exceedsMaxMaterializationsPerMinute = true;
          break;
        default:
          console.error('Unexpected condition', (cond as any).__typename);
          break;
      }
    });
    return results;
  }, [selectedEvaluation]);

  if (loading && !data) {
    return (
      <Box flex={{direction: 'column', grow: 1}}>
        <Box
          padding={{vertical: 8, right: 24, left: 48}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
          flex={{alignItems: 'center', justifyContent: 'space-between'}}
        >
          <Subheading>Result</Subheading>
          <Tag intent="none" icon="spinner">
            Loading…
          </Tag>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box flex={{direction: 'column', grow: 1}}>
        <Box flex={{direction: 'row', justifyContent: 'center'}} padding={24}>
          <ErrorWrapper>{JSON.stringify(error)}</ErrorWrapper>
        </Box>
      </Box>
    );
  }

  if (
    data?.autoMaterializeAssetEvaluationsOrError?.__typename ===
    'AutoMaterializeAssetEvaluationNeedsMigrationError'
  ) {
    return (
      <Box flex={{direction: 'column', grow: 1}}>
        <Box flex={{direction: 'row', justifyContent: 'center'}} padding={{vertical: 24}}>
          <NonIdealState
            icon="error"
            title="Error"
            description={data.autoMaterializeAssetEvaluationsOrError.message}
          />
        </Box>
      </Box>
    );
  }

  return (
    <Box flex={{direction: 'column', grow: 1}}>
      <Box
        padding={{vertical: 8, right: 24, left: 48}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        flex={{alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Subheading>Result</Subheading>
        <Box>
          {selectedEvaluation?.numSkipped || selectedEvaluation?.numDiscarded ? (
            <Tag intent="warning">Skipped</Tag>
          ) : (
            <>
              {selectedEvaluation?.numRequested ? (
                <Tag intent="primary">
                  {selectedEvaluation?.numRequested} run
                  {selectedEvaluation?.numRequested === 1 ? '' : 's'} requested
                </Tag>
              ) : (
                <Tag intent="none">No materialization conditions met</Tag>
              )}
            </>
          )}
        </Box>
      </Box>
      <CollapsibleSection header="Materialization conditions met">
        <Box flex={{direction: 'column', gap: 8}}>
          <Condition
            text="Materialization is missing"
            met={!!conditionResults.materializationIsMissing}
          />
          <Condition
            text="Upstream data has changed since latest materialization"
            met={!!conditionResults.upstreamDataHasChangedSinceLatestMaterialization}
          />
          <Condition
            text="Required to meet this asset's freshness policy"
            met={!!conditionResults.requiredToMeetAFreshnessPolicy}
          />
          <Condition
            text="Required to meet a downstream freshness policy"
            met={!!conditionResults.requiredToMeetADownstreamFreshnessPolicy}
          />
        </Box>
      </CollapsibleSection>
      <CollapsibleSection header="Skip conditions met">
        <Box flex={{direction: 'column', gap: 8}}>
          <Condition
            text="Waiting on upstream data"
            met={!!conditionResults.waitingOnUpstreamData}
            skip={true}
          />
          <Condition
            text={`Exceeds ${maxMaterializationsPerMinute} materializations per minute`}
            met={!!conditionResults.exceedsMaxMaterializationsPerMinute}
            skip={true}
          />
        </Box>
      </CollapsibleSection>
    </Box>
  );
};

const CollapsibleSection = ({
  header,
  headerRightSide,
  children,
}: {
  header: React.ReactNode;
  headerRightSide?: React.ReactNode;
  children: React.ReactNode;
}) => {
  const [isCollapsed, setIsCollapsed] = React.useState(false);

  return (
    <Box
      flex={{direction: 'column'}}
      border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
    >
      <CenterAlignedRow
        flex={{
          justifyContent: 'space-between',
          gap: 12,
          grow: 1,
        }}
        padding={{vertical: 8, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <CenterAlignedRow
          flex={{gap: 8, grow: 1}}
          onClick={() => {
            setIsCollapsed(!isCollapsed);
          }}
          style={{cursor: 'pointer', outline: 'none'}}
          tabIndex={0}
        >
          <Icon
            name="arrow_drop_down"
            style={{transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)'}}
          />
          <Subheading>{header}</Subheading>
        </CenterAlignedRow>
        {headerRightSide}
      </CenterAlignedRow>
      {isCollapsed ? null : <Box padding={{vertical: 12, horizontal: 24}}>{children}</Box>}
    </Box>
  );
};

const Condition = ({
  text,
  met,
  skip = false,
}: {
  text: React.ReactNode;
  met: boolean;
  details?: React.ReactNode;
  skip?: boolean;
}) => {
  const activeColor = skip ? Colors.Yellow700 : Colors.Green700;
  return (
    <CenterAlignedRow flex={{justifyContent: 'space-between'}}>
      <CenterAlignedRow flex={{gap: 8}}>
        <Icon name={met ? 'done' : 'close'} color={met ? activeColor : Colors.Gray400} />
        <div style={{color: met ? activeColor : undefined}}>{text}</div>
      </CenterAlignedRow>
      <div />
    </CenterAlignedRow>
  );
};

const CenterAlignedRow = React.forwardRef((props: React.ComponentProps<typeof Box>, ref) => {
  return (
    <Box
      {...props}
      ref={ref}
      flex={{
        direction: 'row',
        alignItems: 'center',
        ...(props.flex || {}),
      }}
    />
  );
});

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
        }
      }
    }
  }
`;

const AutomaterializePage = styled(Box)`
  a span {
    white-space: normal;
  }
`;
