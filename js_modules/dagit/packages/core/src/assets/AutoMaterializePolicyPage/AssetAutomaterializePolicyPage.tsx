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
  Tooltip,
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

type EvaluationType = GetEvaluationsQuery['autoMaterializeAssetEvaluations'][0];

// This function exists mostly to use the return type later
function useEvaluationsQueryResult({assetKey}: {assetKey: AssetKey}) {
  return useCursorPaginatedQuery<GetEvaluationsQuery, GetEvaluationsQueryVariables>({
    nextCursorForResult: (data) => {
      return data.autoMaterializeAssetEvaluations[PAGE_SIZE - 1]?.evaluationId.toString();
    },
    getResultArray: (data) => {
      return data?.autoMaterializeAssetEvaluations || [];
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

  const evaluations = React.useMemo(() => {
    return queryResult.data?.autoMaterializeAssetEvaluations || [];
  }, [queryResult.data?.autoMaterializeAssetEvaluations]);

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
              queryResult={queryResult}
              paginationProps={paginationProps}
              onSelectEvaluation={(evaluation) => {
                setSelectedEvaluationId(evaluation.evaluationId.toString());
              }}
              selectedEvaluation={selectedEvaluation}
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

export const PAGE_SIZE = 30;
function LeftPanel({
  evaluations,
  queryResult,
  paginationProps,
  onSelectEvaluation,
  selectedEvaluation,
}: {
  evaluations: EvaluationType[];
  queryResult: ReturnType<typeof useEvaluationsQueryResult>['queryResult'];
  paginationProps: ReturnType<typeof useEvaluationsQueryResult>['paginationProps'];
  onSelectEvaluation: (evaluation: EvaluationType) => void;
  selectedEvaluation?: EvaluationType;
}) {
  return (
    <Box flex={{direction: 'column', grow: 1}} style={{overflowY: 'auto'}}>
      <Box style={{flex: 1, minHeight: 0, overflowY: 'auto'}} flex={{grow: 1, direction: 'column'}}>
        {evaluations.map((evaluation) => {
          const isSelected = selectedEvaluation === evaluation;
          return (
            <EvaluationRow
              flex={{justifyContent: 'space-between'}}
              key={evaluation.evaluationId}
              padding={{horizontal: 24, vertical: 8}}
              border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
              onClick={() => {
                onSelectEvaluation(evaluation);
              }}
              $selected={isSelected}
            >
              <TimestampDisplay timestamp={evaluation.timestamp} />
              {evaluation.numRequested ? (
                <Icon name="auto_materialize_policy" size={24} />
              ) : evaluation.numSkipped ? (
                <div
                  style={{
                    margin: '7px',
                    borderRadius: '50%',
                    height: '10px',
                    width: '10px',
                    background: Colors.Yellow500,
                  }}
                />
              ) : (
                <div
                  style={{
                    margin: '7px',
                    borderRadius: '50%',
                    height: '10px',
                    width: '10px',
                    background: Colors.Yellow50,
                  }}
                />
              )}
            </EvaluationRow>
          );
        })}
      </Box>
      {queryResult.data?.autoMaterializeAssetEvaluations?.length ? (
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
              <RightPanelDetail title="Maximum lag minutes" tooltip="test" value={2} />
              <Box flex={{direction: 'column', gap: 8}}>
                This asset will be considered late if it is not materialized within 2 minutes of
                it’s upstream dependencies.
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
  tooltip,
  value,
}: {
  title: React.ReactNode;
  tooltip?: React.ReactNode;
  value: React.ReactNode;
}) => {
  return (
    <Box flex={{direction: 'column', gap: 2}}>
      <CenterAlignedRow flex={{gap: 6}}>
        {title}{' '}
        <Tooltip content={<>{tooltip}</>} position="top">
          <Icon name="info" />
        </Tooltip>
      </CenterAlignedRow>
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
    return data?.autoMaterializeAssetEvaluations[0];
  }, [data?.autoMaterializeAssetEvaluations]);

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
            text="Required to meet a freshness policy"
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
          />
          <Condition
            text={`Exceeds ${maxMaterializationsPerMinute} materializations per minute`}
            met={!!conditionResults.exceedsXMaterializationsPerHour}
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
}: {
  text: React.ReactNode;
  met: boolean;
  details?: React.ReactNode;
}) => {
  return (
    <CenterAlignedRow flex={{justifyContent: 'space-between'}}>
      <CenterAlignedRow flex={{gap: 8}}>
        <Icon name={met ? 'done' : 'close'} color={met ? Colors.Green700 : Colors.Gray400} />
        <div style={{color: met ? Colors.Green700 : undefined}}>{text}</div>
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
    autoMaterializeAssetEvaluations(assetKey: $assetKey, limit: $limit, cursor: $cursor) {
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
`;

const AutomaterializePage = styled(Box)`
  a span {
    white-space: normal;
  }
`;
