import {gql, useQuery} from '@apollo/client';
import {
  Body,
  Box,
  Colors,
  CursorPaginationControls,
  ExternalAnchorButton,
  Icon,
  NonIdealState,
  Spinner,
  Mono,
  Subheading,
  Tag,
} from '@dagster-io/ui';
import dayjs from 'dayjs';
import LocalizedFormat from 'dayjs/plugin/localizedFormat';
import React from 'react';
import {Redirect} from 'react-router';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {ErrorWrapper} from '../../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useCursorPaginatedQuery} from '../../runs/useCursorPaginatedQuery';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {
  AutomaterializePolicyTag,
  automaterializePolicyDescription,
} from '../AutomaterializePolicyTag';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';
import {AssetKey} from '../types';

import {
  GetEvaluationsQuery,
  GetEvaluationsQueryVariables,
  GetPolicyInfoQuery,
  GetPolicyInfoQueryVariables,
} from './types/AssetAutomaterializePolicyPage.types';

dayjs.extend(LocalizedFormat);

type EvaluationType = Extract<
  GetEvaluationsQuery['autoMaterializeAssetEvaluationsOrError'],
  {__typename: 'AutoMaterializeAssetEvaluationRecords'}
>['records'][0];

// This function exists mostly to use the return type later
function useEvaluationsQueryResult({assetKey}: {assetKey: AssetKey}) {
  return useCursorPaginatedQuery<GetEvaluationsQuery, GetEvaluationsQueryVariables>({
    nextCursorForResult: (data) => {
      if (
        data.autoMaterializeAssetEvaluationsOrError?.__typename ===
        'AutoMaterializeAssetEvaluationRecords'
      ) {
        return data.autoMaterializeAssetEvaluationsOrError.records[
          PAGE_SIZE - 1
        ]?.evaluationId.toString();
      }
      return undefined;
    },
    getResultArray: (data) => {
      if (
        data?.autoMaterializeAssetEvaluationsOrError?.__typename ===
        'AutoMaterializeAssetEvaluationRecords'
      ) {
        return data.autoMaterializeAssetEvaluationsOrError.records;
      }
      return [];
    },
    variables: {
      assetKey,
    },
    query: GET_EVALUATIONS_QUERY,
    pageSize: PAGE_SIZE,
  });
}

export const AssetAutomaterializePolicyPage = ({assetKey}: {assetKey: AssetKey}) => {
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

  const [selectedEvaluationId, setSelectedEvaluationId] = useQueryPersistedState<
    number | undefined
  >({
    queryKey: 'evaluation',
    decode: (raw) => {
      const value = parseInt(raw.evaluation);
      return isNaN(value) ? undefined : value;
    },
  });

  const selectedEvaluation: EvaluationType | undefined = React.useMemo(() => {
    if (selectedEvaluationId) {
      return evaluations.find((evaluation) => evaluation.evaluationId === selectedEvaluationId);
    }
    return evaluations[0];
  }, [selectedEvaluationId, evaluations]);

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
          <Subheading>Evaluation History</Subheading>
        </CenterAlignedRow>
        <Box flex={{direction: 'row'}} style={{flex: 1, minHeight: 0}}>
          <Box
            border={{side: 'right', color: Colors.KeylineGray, width: 1}}
            flex={{grow: 0, direction: 'column'}}
            style={{width: '296px'}}
          >
            <LeftPanel
              evaluations={evaluations}
              paginationProps={paginationProps}
              onSelectEvaluation={(evaluation) => {
                setSelectedEvaluationId(evaluation.evaluationId);
              }}
              selectedEvaluation={selectedEvaluation}
              currentEvaluationId={currentEvaluationId}
              isFirstPage={!paginationProps.hasPrevCursor}
              isLastPage={!paginationProps.hasNextCursor}
              isLoading={queryResult.loading && !queryResult.data}
            />
          </Box>
          <Box flex={{grow: 1}} style={{minHeight: 0}}>
            <MiddlePanel
              assetKey={assetKey}
              key={selectedEvaluation?.evaluationId || ''}
              maxMaterializationsPerMinute={maxMaterializationsPerMinute}
              selectedEvaluationId={selectedEvaluationId}
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

export function getEvaluationsWithSkips({
  isLoading,
  currentEvaluationId,
  evaluations,
  isFirstPage,
  isLastPage,
}: {
  evaluations: EvaluationType[];
  currentEvaluationId: number | null;
  isFirstPage: boolean;
  isLastPage: boolean;
  isLoading: boolean;
}) {
  if (isLoading || !currentEvaluationId) {
    return [];
  }
  const evalsWithSkips = [];
  let current = isFirstPage ? currentEvaluationId : evaluations[0]?.evaluationId || 1;
  for (let i = 0; i < evaluations.length; i++) {
    const evaluation = evaluations[i];
    const prevEvaluation = evaluations[i - 1];
    if (evaluation.evaluationId !== current) {
      evalsWithSkips.push({
        __typename: 'no_conditions_met' as const,
        amount: current - evaluation.evaluationId,
        endTimestamp: prevEvaluation?.timestamp ? prevEvaluation?.timestamp - 60 : ('now' as const),
        startTimestamp: evaluation.timestamp + 60,
      });
    }
    evalsWithSkips.push(evaluation);
    current = evaluation.evaluationId - 1;
  }
  if (isLastPage && current > 0) {
    const lastEvaluation = evaluations[evaluations.length - 1];
    evalsWithSkips.push({
      __typename: 'no_conditions_met' as const,
      amount: current - 0,
      endTimestamp: lastEvaluation?.timestamp ? lastEvaluation?.timestamp - 60 : ('now' as const),
      startTimestamp: 0,
    });
  }
  return evalsWithSkips;
}

export const PAGE_SIZE = 30;
function LeftPanel({
  evaluations,
  paginationProps,
  onSelectEvaluation,
  selectedEvaluation,
  currentEvaluationId,
  isFirstPage,
  isLastPage,
  isLoading,
}: {
  evaluations: EvaluationType[];
  paginationProps: ReturnType<typeof useEvaluationsQueryResult>['paginationProps'];
  onSelectEvaluation: (evaluation: EvaluationType) => void;
  selectedEvaluation?: EvaluationType;
  currentEvaluationId: number | null;
  isFirstPage: boolean;
  isLastPage: boolean;
  isLoading: boolean;
}) {
  const evaluationsWithSkips = React.useMemo(
    () =>
      getEvaluationsWithSkips({
        currentEvaluationId,
        evaluations,
        isFirstPage,
        isLastPage,
        isLoading,
      }),
    [currentEvaluationId, evaluations, isFirstPage, isLastPage, isLoading],
  );

  return (
    <Box flex={{direction: 'column', grow: 1}} style={{overflowY: 'auto'}}>
      <Box style={{flex: 1, minHeight: 0, overflowY: 'auto'}} flex={{grow: 1, direction: 'column'}}>
        {evaluationsWithSkips.map((evaluation) => {
          if (evaluation.__typename === 'no_conditions_met') {
            return (
              <EvaluationRow
                style={{cursor: 'default'}}
                key={`skip-${evaluation.endTimestamp}`}
                flex={{direction: 'column'}}
              >
                <Box
                  padding={{left: 16}}
                  border={{side: 'left', width: 1, color: Colors.KeylineGray}}
                  flex={{direction: 'column', gap: 4}}
                  style={{width: '100%'}}
                >
                  <div>No materialization conditions met </div>
                  <div>
                    {evaluation.startTimestamp ? (
                      <>
                        <TimestampDisplay timestamp={evaluation.startTimestamp} />
                        {' - '}
                      </>
                    ) : (
                      'Before '
                    )}
                    {evaluation.endTimestamp === 'now' ? (
                      'now'
                    ) : (
                      <TimestampDisplay timestamp={evaluation.endTimestamp} />
                    )}
                  </div>
                </Box>
              </EvaluationRow>
            );
          }
          const isSelected = selectedEvaluation === evaluation;
          if (evaluation.numSkipped) {
            return (
              <EvaluationRow
                style={{cursor: 'default'}}
                key={`skip-${evaluation.timestamp}`}
                onClick={() => {
                  onSelectEvaluation(evaluation);
                }}
                $selected={isSelected}
              >
                <Box
                  padding={{left: 16}}
                  border={{side: 'left', width: 1, color: Colors.KeylineGray}}
                  flex={{direction: 'column', gap: 4}}
                  style={{width: '100%'}}
                >
                  <div style={{color: Colors.Yellow700}}>
                    {evaluation.numSkipped} materialization{evaluation.numSkipped === 1 ? '' : 's'}{' '}
                    skipped{' '}
                  </div>
                  <TimestampDisplay timestamp={evaluation.timestamp} />
                </Box>
              </EvaluationRow>
            );
          }
          return (
            <EvaluationRow
              key={evaluation.evaluationId}
              onClick={() => {
                onSelectEvaluation(evaluation);
              }}
              $selected={isSelected}
            >
              <Box
                flex={{direction: 'row', gap: 8}}
                style={{color: Colors.Blue700, marginLeft: '-8px'}}
              >
                <Icon name="done" color={Colors.Blue700} />
                <Box flex={{direction: 'column', gap: 4}} style={{width: '100%'}}>
                  <div>
                    {evaluation.numRequested} run{evaluation.numRequested === 1 ? '' : 's'}{' '}
                    requested
                  </div>
                  <TimestampDisplay timestamp={evaluation.timestamp} />
                </Box>
              </Box>
            </EvaluationRow>
          );
        })}
      </Box>
      {evaluations.length ? (
        <PaginationWrapper>
          <CursorPaginationControls {...paginationProps} />
        </PaginationWrapper>
      ) : null}
    </Box>
  );
}

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
                  Auto-materialize Policy
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
              title="No Automaterialize policy found"
              shrinkable
              description={
                <Box flex={{direction: 'column', gap: 8}}>
                  <div>
                    An AutoMaterializePolicy specifies how Dagster should attempt to keep an asset
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
  selectedEvaluationId,
  maxMaterializationsPerMinute,
}: {
  assetKey: Omit<AssetKey, '__typename'>;
  selectedEvaluationId?: number;
  maxMaterializationsPerMinute: number;
}) => {
  const {data, loading, error} = useQuery<GetEvaluationsQuery, GetEvaluationsQueryVariables>(
    GET_EVALUATIONS_QUERY,
    {
      variables: {
        assetKey,
        cursor: selectedEvaluationId ? (selectedEvaluationId + 1).toString() : undefined,
        limit: 2,
      },
    },
  );

  const evaluationData = React.useMemo(() => {
    if (
      data?.autoMaterializeAssetEvaluationsOrError?.__typename ===
      'AutoMaterializeAssetEvaluationRecords'
    ) {
      return data?.autoMaterializeAssetEvaluationsOrError.records[0];
    }
    return null;
  }, [data?.autoMaterializeAssetEvaluationsOrError]);

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
      exceedsXMaterializationsPerHour: boolean;
    }> = {};
    evaluationData?.conditions.forEach((cond) => {
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
          results.exceedsXMaterializationsPerHour = true;
          break;
        default:
          console.error('Unexpected condition', (cond as any).__typename);
          break;
      }
    });
    return results;
  }, [evaluationData]);

  if (loading) {
    return (
      <Box flex={{direction: 'column', grow: 1}}>
        <Box flex={{direction: 'row', justifyContent: 'center'}} padding={{vertical: 24}}>
          <Spinner purpose="section" />
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

  if (!evaluationData) {
    if (selectedEvaluationId) {
      return (
        <Box flex={{direction: 'column', grow: 1}}>
          <Box flex={{direction: 'row', justifyContent: 'center'}} padding={{vertical: 24}}>
            <NonIdealState
              icon="auto_materialize_policy"
              title="Evaluation not found"
              description={
                <>
                  No evaluation with ID <Mono>{selectedEvaluationId}</Mono> found
                </>
              }
            />
          </Box>
        </Box>
      );
    } else {
      return (
        <Box flex={{direction: 'column', grow: 1}}>
          <Box flex={{direction: 'row', justifyContent: 'center'}} padding={{vertical: 24}}>
            <NonIdealState
              icon="auto_materialize_policy"
              title="No evaluations found"
              description={
                <Box flex={{direction: 'column', gap: 8}}>
                  <div>
                    You can set up Dagster to automatically materialize assets when criteria are
                    met.
                  </div>
                  <div>
                    <ExternalAnchorButton
                      icon={<Icon name="open_in_new" />}
                      href="https://docs.dagster.io/concepts/assets/asset-auto-execution"
                    >
                      View documentation
                    </ExternalAnchorButton>
                  </div>
                </Box>
              }
            />
          </Box>
        </Box>
      );
    }
  }

  return (
    <Box flex={{direction: 'column', grow: 1}}>
      <Box
        padding={{vertical: 8, right: 24, left: 48}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        flex={{justifyContent: 'space-between'}}
      >
        <Subheading>Result</Subheading>
        <Box>
          {evaluationData.numRequested > 0 ? (
            <Tag intent="primary">
              {evaluationData.numRequested} run{evaluationData.numRequested === 1 ? '' : 's'}{' '}
              requested
            </Tag>
          ) : (
            <Tag intent="warning">Skipped</Tag>
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
            met={!!conditionResults.exceedsXMaterializationsPerHour}
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
            style={{transform: isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)'}}
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

export const GET_EVALUATIONS_QUERY = gql`
  query GetEvaluationsQuery($assetKey: AssetKeyInput!, $limit: Int!, $cursor: String) {
    autoMaterializeAssetEvaluationsOrError(assetKey: $assetKey, limit: $limit, cursor: $cursor) {
      ... on AutoMaterializeAssetEvaluationRecords {
        currentEvaluationId
        records {
          id
          evaluationId
          numRequested
          numSkipped
          numDiscarded
          timestamp
          conditions {
            ... on AutoMaterializeConditionWithDecisionType {
              decisionType
            }
          }
        }
      }
      ... on AutoMaterializeAssetEvaluationNeedsMigrationError {
        message
      }
    }
  }
`;

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
const PaginationWrapper = styled.div`
  position: sticky;
  bottom: 0;
  background: ${Colors.White};
  border-right: 1px solid ${Colors.KeylineGray};
  box-shadow: inset 0 1px ${Colors.KeylineGray};
  margin-top: -1px;
  padding-bottom: 16px;
  padding-top: 16px;
  > * {
    margin-top: 0;
  }
`;

const EvaluationRow = styled(CenterAlignedRow)<{$selected: boolean}>`
  cursor: pointer;
  &:hover {
    background: ${Colors.Gray10};
  }
  &,
  &:hover {
    ${({$selected}) =>
      $selected
        ? `
    background: ${Colors.Blue50};
  `
        : null}
    width: 295px;
  }
  padding: 8px 24px;
  border-bottom: 1px solid ${Colors.KeylineGray};
`;

const AutomaterializePage = styled(Box)`
  a span {
    white-space: normal;
  }
`;
