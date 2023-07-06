import {useQuery} from '@apollo/client';
import {Box, Colors, Subheading, Icon, NonIdealState} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ErrorWrapper} from '../../app/PythonErrorInfo';
import {AssetKey} from '../types';

import {AutomaterializeRequestedPartitionsLink} from './AutomaterializeRequestedPartitionsLink';
import {AutomaterializeRunTag} from './AutomaterializeRunTag';
import {GET_EVALUATIONS_QUERY} from './GetEvaluationsQuery';
import {EvaluationOrEmpty} from './types';
import {
  AutoMateralizeWithConditionFragment,
  GetEvaluationsQuery,
  GetEvaluationsQueryVariables,
} from './types/GetEvaluationsQuery.types';

const isRequestCondition = (
  condition: AutoMateralizeWithConditionFragment,
): condition is AutoMateralizeWithConditionFragment => {
  switch (condition.__typename) {
    case 'MissingAutoMaterializeCondition':
    case 'DownstreamFreshnessAutoMaterializeCondition':
    case 'FreshnessAutoMaterializeCondition':
    case 'ParentMaterializedAutoMaterializeCondition':
      return true;
    default:
      return false;
  }
};

type ConditionType = AutoMateralizeWithConditionFragment['__typename'];

const extractRequestedPartitionKeys = (conditions: AutoMateralizeWithConditionFragment[]) => {
  let requested: string[] = [];
  let skippedOrDiscarded: string[] = [];

  conditions.forEach((condition) => {
    const didRequest = isRequestCondition(condition);
    const partitionKeys =
      condition.partitionKeysOrError?.__typename === 'PartitionKeys'
        ? condition.partitionKeysOrError.partitionKeys
        : [];
    if (didRequest) {
      requested = requested.concat(partitionKeys);
    } else {
      skippedOrDiscarded = skippedOrDiscarded.concat(partitionKeys);
    }
  });

  const skippedOrDiscardedSet = new Set(skippedOrDiscarded);
  return new Set(requested.filter((partitionKey) => !skippedOrDiscardedSet.has(partitionKey)));
};

interface Props {
  assetKey: AssetKey;
  assetHasDefinedPartitions: boolean;
  selectedEvaluation?: EvaluationOrEmpty;
  maxMaterializationsPerMinute: number;
}

export const AutomaterializeMiddlePanel = ({
  assetKey,
  assetHasDefinedPartitions,
  selectedEvaluation,
  maxMaterializationsPerMinute,
}: Props) => {
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

  const conditionToPartitions: Record<ConditionType, string[]> = React.useMemo(() => {
    const conditions = selectedEvaluation?.conditions;
    if (!conditions?.length) {
      return {} as Record<ConditionType, string[]>;
    }
    return Object.fromEntries(
      conditions
        .map((condition) => {
          const {__typename, partitionKeysOrError} = condition;
          if (partitionKeysOrError?.__typename === 'PartitionKeys') {
            return [__typename, partitionKeysOrError.partitionKeys];
          }
          return null;
        })
        .filter((entryOrNull): entryOrNull is [ConditionType, string[]] => !!entryOrNull),
    ) as Record<ConditionType, string[]>;
  }, [selectedEvaluation]);

  const conditionResults = React.useMemo(() => {
    if (assetHasDefinedPartitions) {
      return new Set(Object.keys(conditionToPartitions));
    }
    return new Set(selectedEvaluation?.conditions?.map((condition) => condition.__typename) || []);
  }, [assetHasDefinedPartitions, conditionToPartitions, selectedEvaluation]);

  if (loading && !data) {
    return (
      <Box flex={{direction: 'column', grow: 1}}>
        <Box
          style={{flex: '0 0 48px'}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
          padding={{horizontal: 16}}
          flex={{alignItems: 'center', justifyContent: 'space-between'}}
        >
          <Subheading>Result</Subheading>
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

  const headerRight = () => {
    const runIds =
      selectedEvaluation?.__typename === 'AutoMaterializeAssetEvaluationRecord'
        ? selectedEvaluation.runIds
        : [];
    const count = runIds.length;

    if (count === 0 || !selectedEvaluation?.conditions) {
      return null;
    }

    const {conditions} = selectedEvaluation;
    if (assetHasDefinedPartitions) {
      const partitionKeys = extractRequestedPartitionKeys(conditions);
      return (
        <AutomaterializeRequestedPartitionsLink
          runIds={runIds}
          partitionKeys={Array.from(partitionKeys)}
        />
      );
    }

    return <AutomaterializeRunTag runId={runIds[0]!} />;
  };

  return (
    <Box flex={{direction: 'column', grow: 1}}>
      <Box
        style={{flex: '0 0 48px'}}
        padding={{horizontal: 16}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        flex={{alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Subheading>Result</Subheading>
        <div>{headerRight()}</div>
      </Box>
      <CollapsibleSection header="Materialization conditions met">
        <Box flex={{direction: 'column', gap: 8}}>
          <Condition
            text="Materialization is missing"
            met={conditionResults.has('MissingAutoMaterializeCondition')}
            type="materialization"
            assetHasDefinedPartitions={assetHasDefinedPartitions}
            partitionKeys={conditionToPartitions['MissingAutoMaterializeCondition']}
          />
          <Condition
            text="Upstream data has changed since latest materialization"
            met={conditionResults.has('ParentMaterializedAutoMaterializeCondition')}
            type="materialization"
            assetHasDefinedPartitions={assetHasDefinedPartitions}
            partitionKeys={conditionToPartitions['ParentMaterializedAutoMaterializeCondition']}
          />
          <Condition
            text="Required to meet this asset's freshness policy"
            met={conditionResults.has('FreshnessAutoMaterializeCondition')}
            type="materialization"
            assetHasDefinedPartitions={assetHasDefinedPartitions}
            partitionKeys={conditionToPartitions['FreshnessAutoMaterializeCondition']}
          />
          <Condition
            text="Required to meet a downstream freshness policy"
            met={conditionResults.has('DownstreamFreshnessAutoMaterializeCondition')}
            type="materialization"
            assetHasDefinedPartitions={assetHasDefinedPartitions}
            partitionKeys={conditionToPartitions['DownstreamFreshnessAutoMaterializeCondition']}
          />
        </Box>
      </CollapsibleSection>
      <CollapsibleSection header="Skip conditions met">
        <Condition
          text="Waiting on upstream data"
          met={conditionResults.has('ParentOutdatedAutoMaterializeCondition')}
          type="skip"
          assetHasDefinedPartitions={assetHasDefinedPartitions}
          partitionKeys={conditionToPartitions['ParentOutdatedAutoMaterializeCondition']}
        />
      </CollapsibleSection>
      <CollapsibleSection header="Discard conditions met">
        <Condition
          text={`Exceeds ${
            maxMaterializationsPerMinute === 1
              ? '1 materialization'
              : `${maxMaterializationsPerMinute} materializations`
          } per minute`}
          met={conditionResults.has('MaxMaterializationsExceededAutoMaterializeCondition')}
          type="discard"
          assetHasDefinedPartitions={assetHasDefinedPartitions}
          partitionKeys={
            conditionToPartitions['MaxMaterializationsExceededAutoMaterializeCondition']
          }
        />
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
      <SectionHeader onClick={() => setIsCollapsed(!isCollapsed)}>
        <Box
          flex={{
            justifyContent: 'space-between',
            gap: 12,
            grow: 1,
          }}
          padding={{vertical: 8, horizontal: 16}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <CenterAlignedRow flex={{gap: 4, grow: 1}}>
            <Icon
              name="arrow_drop_down"
              style={{transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)'}}
            />
            <Subheading>{header}</Subheading>
          </CenterAlignedRow>
          {headerRightSide}
        </Box>
      </SectionHeader>
      {isCollapsed ? null : <Box padding={{vertical: 12, left: 32, right: 16}}>{children}</Box>}
    </Box>
  );
};

const Condition = ({
  text,
  met,
  type,
  partitionKeys,
  assetHasDefinedPartitions,
}: {
  text: React.ReactNode;
  met: boolean;
  details?: React.ReactNode;
  type: 'materialization' | 'skip' | 'discard';
  partitionKeys: string[] | undefined;
  assetHasDefinedPartitions: boolean;
}) => {
  const activeColor = React.useMemo(() => {
    switch (type) {
      case 'skip':
        return Colors.Yellow700;
      case 'discard':
        return Colors.Red700;
      default:
        return Colors.Green700;
    }
  }, [type]);

  return (
    <CenterAlignedRow flex={{justifyContent: 'space-between'}}>
      <CenterAlignedRow flex={{gap: 8}}>
        <Icon name={met ? 'done' : 'close'} color={met ? activeColor : Colors.Gray400} />
        <div style={{color: met ? activeColor : undefined}}>{text}</div>
      </CenterAlignedRow>
      {assetHasDefinedPartitions ? (
        partitionKeys?.length ? (
          <AutomaterializeRequestedPartitionsLink partitionKeys={partitionKeys} />
        ) : (
          <div style={{color: Colors.Gray400}}>&ndash;</div>
        )
      ) : null}
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

const SectionHeader = styled.button`
  background-color: ${Colors.White};
  border: 0;
  cursor: pointer;
  padding: 0;
  margin: 0;

  :focus {
    outline: none;
  }
`;
