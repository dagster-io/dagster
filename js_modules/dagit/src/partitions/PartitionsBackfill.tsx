import * as React from "react";
import gql from "graphql-tag";
import { useQuery, useMutation } from "react-apollo";
import { useRepositorySelector } from "../DagsterRepositoryContext";
import { LaunchButton } from "../execute/LaunchButton";
import { PartitionsNameQuery } from "./types/PartitionsNameQuery";
import {
  Colors,
  Checkbox,
  Collapse,
  Divider,
  Icon,
  Intent,
  NonIdealState,
  ProgressBar,
  Spinner
} from "@blueprintjs/core";
import styled from "styled-components";
import PythonErrorInfo from "../PythonErrorInfo";
import { GraphQueryInput } from "../GraphQueryInput";
import { RUN_STATUS_COLORS } from "../runs/RunStatusDots";
import { filterByQuery } from "../GraphQueryImpl";
import { GaantChartMode } from "../gaant/GaantChart";
import { buildLayout } from "../gaant/GaantChartLayout";
import {
  PartitionFailedSelectorPipelineQuery,
  PartitionFailedSelectorPipelineQueryVariables
} from "./types/PartitionFailedSelectorPipelineQuery";
import {
  PartitionStepSelectorPipelineQuery,
  PartitionStepSelectorPipelineQueryVariables
} from "./types/PartitionStepSelectorPipelineQuery";
import { Header } from "../ListComponents";
import { PipelineRunStatus } from "../types/globalTypes";
import { IconNames } from "@blueprintjs/icons";
import { SharedToaster } from "../DomUtils";

const LaunchBackfillButton: React.FunctionComponent<{
  partitionSetName: string;
  partitionNames: string[];
  reexecutionSteps?: string[];
  fromFailure?: boolean;
  onSuccess?: (backfillId: string) => void;
  onError?: () => void;
}> = ({ partitionSetName, partitionNames, reexecutionSteps, fromFailure, onSuccess, onError }) => {
  const repositorySelector = useRepositorySelector();
  const mounted = React.useRef(true);
  const [launchBackfill] = useMutation(LAUNCH_PARTITION_BACKFILL_MUTATION);
  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, [onSuccess]);
  const onLaunch = async () => {
    const { data } = await launchBackfill({
      variables: {
        backfillParams: {
          selector: {
            partitionSetName,
            repositorySelector
          },
          partitionNames,
          reexecutionSteps,
          fromFailure
        }
      }
    });

    if (!mounted.current) {
      return;
    }

    if (data && data.launchPartitionBackfill.__typename === "PartitionBackfillSuccess") {
      onSuccess?.(data.launchPartitionBackfill.backfillId);
    } else {
      onError?.();
    }
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "flex-end",
        alignItems: "center",
        margin: "20px 0"
      }}
    >
      <LaunchButton
        config={{
          title: partitionNames.length
            ? partitionNames.length === 1
              ? "Launch 1 run"
              : `Launch ${partitionNames.length} runs`
            : "Launch",
          icon: "send-to",
          disabled: !partitionNames.length,
          tooltip: partitionNames.length
            ? partitionNames.length === 1
              ? "Launch 1 run"
              : `Launch ${partitionNames.length} runs`
            : "Select runs to launch",
          onClick: onLaunch
        }}
      />
    </div>
  );
};

export const PartitionsBackfill: React.FunctionComponent<{
  partitionSetName: string;
  showLoader: boolean;
  onLaunch?: (backfillId: string) => void;
}> = ({ partitionSetName, showLoader, onLaunch }) => {
  const repositorySelector = useRepositorySelector();
  const mounted = React.useRef(true);
  const [backfillType, setType] = React.useState<string>("");
  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, [onLaunch]);
  const { loading, data } = useQuery<PartitionsNameQuery>(PARTITIONS_NAME_QUERY, {
    variables: { repositorySelector, partitionSetName },
    fetchPolicy: "network-only"
  });

  if ((!data || loading) && showLoader) {
    return (
      <div
        style={{
          maxWidth: 600,
          margin: "10px auto"
        }}
      >
        <ProgressBar />
      </div>
    );
  }

  if (!data || loading) {
    return <div />;
  }

  const { partitionSetOrError } = data;
  if (partitionSetOrError.__typename === "PartitionSetNotFoundError") {
    return (
      <NonIdealState
        icon={IconNames.ERROR}
        title="Partition Set Not Found"
        description={partitionSetOrError.message}
      />
    );
  }

  if (partitionSetOrError.__typename !== "PartitionSet") {
    return <div />;
  }
  if (partitionSetOrError.partitionsOrError.__typename !== "Partitions") {
    return <div />;
  }

  const partitionNames = partitionSetOrError.partitionsOrError.results.map(x => x.name);
  const onSuccess = (backfillId: string) => {
    SharedToaster.show({
      message: `Created backfill job "${backfillId}"`,
      intent: Intent.SUCCESS
    });
    setType("");
    onLaunch?.(backfillId);
  };
  return (
    <div
      style={{
        marginTop: 30,
        marginBottom: 30,
        paddingBottom: 10
      }}
    >
      <Header>Launch Partition Backfill</Header>
      <Divider />
      <div style={{ marginTop: 20 }}>
        <CollapsibleMenu
          title="Full pipeline execution"
          isOpen={backfillType === "full"}
          onToggle={() => {
            setType(backfillType !== "full" ? "full" : "");
          }}
        >
          <FullPartitionsSelect
            partitionNames={partitionNames}
            partitionSetName={partitionSetName}
            pipelineName={partitionSetOrError.pipelineName}
            onSuccess={onSuccess}
          />
        </CollapsibleMenu>
        <CollapsibleMenu
          title="From last failure"
          isOpen={backfillType === "fromFailure"}
          onToggle={() => {
            setType(backfillType !== "fromFailure" ? "fromFailure" : "");
          }}
        >
          <FailedPartitionsSelect
            partitionNames={partitionNames}
            partitionSetName={partitionSetName}
            pipelineName={partitionSetOrError.pipelineName}
            onSuccess={onSuccess}
          />
        </CollapsibleMenu>
        <CollapsibleMenu
          title="From last successful run"
          isOpen={backfillType === "fromLast"}
          onToggle={() => {
            setType(backfillType !== "fromLast" ? "fromLast" : "");
          }}
        >
          <StepPartitionsSelect
            partitionNames={partitionNames}
            partitionSetName={partitionSetName}
            pipelineName={partitionSetOrError.pipelineName}
            onSuccess={onSuccess}
          />
        </CollapsibleMenu>
      </div>
    </div>
  );
};

const CollapsibleMenu: React.FunctionComponent<{
  title: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}> = ({ title, isOpen, onToggle, children }) => {
  return (
    <>
      <CollapsibleMenuItem isOpen={isOpen} onClick={onToggle}>
        <Icon icon={isOpen ? "chevron-down" : "chevron-right"} />
        <span style={{ marginLeft: 5 }}>{title}</span>
      </CollapsibleMenuItem>
      <Collapse isOpen={isOpen}>
        <CollapseContainer>{children}</CollapseContainer>
      </Collapse>
    </>
  );
};

const FullPartitionsSelect: React.FunctionComponent<{
  partitionNames: string[];
  partitionSetName: string;
  pipelineName: string;
  onSuccess?: (backfillId: string) => void;
}> = ({ partitionNames, partitionSetName, pipelineName, onSuccess }) => {
  const [selected, setSelected] = React.useState<string[]>([]);
  const selectPartition = (name: string) => {
    const newSelected: string[] = selected.includes(name)
      ? selected.filter(x => x !== name)
      : [...selected, name];
    setSelected(newSelected);
  };

  return (
    <div>
      <label style={{ display: "flex" }}>
        <Checkbox
          style={{ marginBottom: 0, marginTop: 1 }}
          checked={selected.length === partitionNames.length}
          onClick={() =>
            setSelected(selected.length === partitionNames.length ? [] : partitionNames)
          }
        />
        Select All
      </label>
      <GridContainer>
        <GridColumn readOnly>
          <LabelTilted></LabelTilted>
          <Label>{pipelineName}</Label>
        </GridColumn>
        <PartitionsContainer>
          {partitionNames.map((partitionName, idx) => (
            <GridColumn
              key={partitionName}
              style={{ zIndex: partitionNames.length - idx }}
              focused={selected.includes(partitionName)}
              onClick={() => selectPartition(partitionName)}
            >
              <LabelTilted>
                <div className="tilted">{partitionName}</div>
              </LabelTilted>
              <Square className="missing" />
            </GridColumn>
          ))}
        </PartitionsContainer>
      </GridContainer>
      <LaunchBackfillButton
        partitionNames={selected}
        partitionSetName={partitionSetName}
        onSuccess={onSuccess}
      />
    </div>
  );
};

const FailedPartitionsSelect: React.FunctionComponent<{
  partitionNames: string[];
  pipelineName: string;
  partitionSetName: string;
  onSuccess?: (backfillId: string) => void;
}> = ({ partitionNames, pipelineName, partitionSetName, onSuccess }) => {
  const [selected, setSelected] = React.useState<string[]>([]);
  const repositorySelector = useRepositorySelector();
  const { data, loading } = useQuery<
    PartitionFailedSelectorPipelineQuery,
    PartitionFailedSelectorPipelineQueryVariables
  >(PARTITION_FAILED_SELECTOR_PIPELINE_QUERY, {
    variables: {
      repositorySelector,
      partitionSetName
    }
  });

  const runPartitions =
    (data?.partitionSetOrError.__typename === "PartitionSet" &&
      data.partitionSetOrError.partitionsOrError.__typename === "Partitions" &&
      data.partitionSetOrError.partitionsOrError.results) ||
    [];
  const selectablePartitions = runPartitions
    .filter(x => x.runs.length && x.runs[0].status === PipelineRunStatus.FAILURE)
    .map(x => x.name);

  const selectPartition = (name: string) => {
    if (!selectablePartitions.includes(name)) {
      return;
    }
    const newSelected: string[] = selected.includes(name)
      ? selected.filter(x => x !== name)
      : [...selected, name];
    setSelected(newSelected);
  };

  if (loading) {
    return <Spinner size={30} />;
  }

  return (
    <div>
      <label style={{ display: "flex" }}>
        <Checkbox
          style={{ marginBottom: 0, marginTop: 1 }}
          checked={selected.length === selectablePartitions.length}
          onClick={() =>
            setSelected(selected.length === selectablePartitions.length ? [] : selectablePartitions)
          }
        />
        Select All
      </label>
      <GridContainer>
        <GridColumn readOnly>
          <LabelTilted></LabelTilted>
          <Label>{pipelineName}</Label>
        </GridColumn>
        <PartitionsContainer>
          {partitionNames.map((partitionName, idx) => (
            <GridColumn
              key={partitionName}
              style={{ zIndex: partitionNames.length - idx }}
              disabled={!selectablePartitions.includes(partitionName)}
              focused={selected.includes(partitionName)}
              onClick={() => selectPartition(partitionName)}
            >
              <LabelTilted>
                <div className="tilted">{partitionName}</div>
              </LabelTilted>
              <Square
                className={selectablePartitions.includes(partitionName) ? "missing" : "disabled"}
              />
            </GridColumn>
          ))}
        </PartitionsContainer>
      </GridContainer>
      <LaunchBackfillButton
        partitionNames={selected}
        partitionSetName={partitionSetName}
        fromFailure={true}
        onSuccess={onSuccess}
      />
    </div>
  );
};

const StepPartitionsSelect: React.FunctionComponent<{
  partitionNames: string[];
  pipelineName: string;
  partitionSetName: string;
  onSuccess?: (backfillId: string) => void;
}> = ({ partitionNames, pipelineName, partitionSetName, onSuccess }) => {
  const [selected, setSelected] = React.useState<string[]>([]);
  const [query, setQuery] = React.useState<string>("");
  const repositorySelector = useRepositorySelector();
  const { data, loading } = useQuery<
    PartitionStepSelectorPipelineQuery,
    PartitionStepSelectorPipelineQueryVariables
  >(PARTITION_STEP_SELECTOR_PIPELINE_QUERY, {
    variables: {
      pipelineSelector: {
        ...repositorySelector,
        pipelineName
      },
      repositorySelector,
      partitionSetName
    }
  });

  const solids =
    data?.pipelineSnapshotOrError.__typename === "PipelineSnapshot" &&
    data.pipelineSnapshotOrError.solidHandles.map((h: any) => h.solid);

  const runPartitions =
    data?.partitionSetOrError.__typename === "PartitionSet" &&
    data.partitionSetOrError.partitionsOrError.__typename === "Partitions" &&
    data.partitionSetOrError.partitionsOrError.results;

  if (loading) {
    return <Spinner size={30} />;
  }
  if (!solids || !runPartitions) {
    return <span />;
  }

  const selectablePartitions = runPartitions
    .filter(x => x.runs.length && x.runs[0].status === PipelineRunStatus.SUCCESS)
    .map(x => x.name);
  const solidsFiltered = filterByQuery(solids, query);
  const layout = buildLayout({ nodes: solidsFiltered.all, mode: GaantChartMode.FLAT });
  const stepRows = layout.boxes.map(box => ({
    x: box.x,
    name: box.node.name
  }));

  const setFocusedPartition = (name: string) => {
    if (!selectablePartitions.includes(name)) {
      return;
    }
    const newSelected: string[] = selected.includes(name)
      ? selected.filter(x => x !== name)
      : [...selected, name];
    setSelected(newSelected);
  };

  return (
    <div>
      <label style={{ display: "flex", marginBottom: 10 }}>
        <Checkbox
          style={{ marginBottom: 0, marginTop: 1 }}
          checked={selected.length === selectablePartitions.length}
          onClick={() =>
            setSelected(selected.length === selectablePartitions.length ? [] : selectablePartitions)
          }
        />
        Select All
      </label>
      <GridContainer>
        <GridColumn readOnly>
          <LabelTilted>
            <GraphQueryInput
              width={260}
              items={solids}
              value={query}
              placeholder="Type a Step Subset"
              onChange={setQuery}
            />
          </LabelTilted>
          {stepRows.map(step => (
            <Label style={{ paddingLeft: step.x }} key={step.name}>
              {step.name}
            </Label>
          ))}
        </GridColumn>
        <PartitionsContainer>
          {partitionNames.map((partitionName, idx) => (
            <GridColumn
              key={partitionName}
              style={{ zIndex: partitionNames.length - idx }}
              disabled={!selectablePartitions.includes(partitionName)}
              focused={selected.includes(partitionName)}
              onClick={() => setFocusedPartition(partitionName)}
            >
              <LabelTilted>
                <div className="tilted">{partitionName}</div>
              </LabelTilted>
              {stepRows.map(step => (
                <Square
                  key={`${partitionName}:${step.name}`}
                  className={selectablePartitions.includes(partitionName) ? "missing" : "disabled"}
                />
              ))}
            </GridColumn>
          ))}
        </PartitionsContainer>
      </GridContainer>
      {stepRows.length === 0 && <EmptyMessage>No data to display.</EmptyMessage>}
      <LaunchBackfillButton
        partitionNames={selected}
        partitionSetName={partitionSetName}
        reexecutionSteps={stepRows.map(step => `${step.name}.compute`)}
        onSuccess={onSuccess}
      />
    </div>
  );
};

const EmptyMessage = styled.div`
  padding: 20px;
  text-align: center;
`;
const Label = styled.div`
  height: 15px;
  margin: 4px;
  font-size: 13px;
`;
const PartitionsContainer = styled.div`
  flex: 1;
  display: flex;
  overflow-x: auto;
  padding-bottom: 20px;
`;

const LabelTilted = styled.div`
  position: relative;
  height: 55px;
  padding: 4px;
  padding-bottom: 0;
  min-width: 15px;
  margin-bottom: 15px;
  align-items: end;
  display: flex;

  & > div.tilted {
    font-size: 12px;
    white-space: nowrap;
    position: absolute;
    bottom: -20px;
    left: 0;
    padding: 2px;
    padding-right: 4px;
    padding-left: 0;
    transform: rotate(-41deg);
    transform-origin: top left;
  }
`;

const GridContainer = styled.div`
  display: flex;
  padding-right: 60px;
`;

const GridColumn = styled.div<{ disabled?: boolean; focused?: boolean; readOnly?: boolean }>`
  display: flex;
  flex-direction: column;
  ${({ disabled, focused, readOnly }) =>
    !disabled &&
    !focused &&
    !readOnly &&
    `&:hover {
    cursor: default;
    background: ${Colors.LIGHT_GRAY4};
    ${LabelTilted} {
      background: ${Colors.WHITE};
      .tilted {
        background: ${Colors.LIGHT_GRAY4};
      }
    }
  }`}
  ${({ focused }) =>
    focused &&
    `background: ${Colors.BLUE4};
    ${Label} {
      color: white;
    }
    ${LabelTilted} {
      background: ${Colors.WHITE};
      color: white;
      .tilted {
        background: ${Colors.BLUE4};
      }
    }
  }`}
  ${({ disabled }) =>
    disabled &&
    `background: ${Colors.WHITE};
    ${Label} {
      color: ${Colors.LIGHT_GRAY1};
    }
    ${LabelTilted} {
      background: ${Colors.WHITE};
      color: ${Colors.LIGHT_GRAY1};;
    }
  }`}
`;

const SUCCESS_COLOR = "#CFE6DC";

const Square = styled.div`
  width: 15px;
  height: 15px;
  margin: 4px;
  display: inline-block;

  &.success {
    background: ${SUCCESS_COLOR};
  }
  &.failure {
    background: ${RUN_STATUS_COLORS.FAILURE};
  }
  &.failure-success {
    background: linear-gradient(135deg, ${RUN_STATUS_COLORS.FAILURE} 40%, ${SUCCESS_COLOR} 41%);
  }
  &.skipped {
    background: ${Colors.GOLD3};
  }
  &.skipped-success {
    background: linear-gradient(135deg, ${Colors.GOLD3} 40%, ${SUCCESS_COLOR} 41%);
  }
  &.missing {
    background: ${Colors.LIGHT_GRAY3};
  }
  &.missing-success {
    background: linear-gradient(135deg, ${Colors.LIGHT_GRAY3} 40%, ${SUCCESS_COLOR} 41%);
  }
  &.disabled {
    background: ${Colors.LIGHT_GRAY5};
  }
`;

const CollapsibleMenuItem = styled.div`
  border: 1px solid #ececec;
  background-color: #fafafa;
  &:hover {
    background-color: #ececec;
  }
  margin-bottom: ${({ isOpen }: { isOpen: boolean }) => (isOpen ? "0" : "5px")};
  cursor: pointer;
  padding: 10px;
  border-radius: 3px;
  border-bottom-right-radius: ${({ isOpen }: { isOpen: boolean }) => (isOpen ? "0" : "3px")};
  border-bottom-left-radius: ${({ isOpen }: { isOpen: boolean }) => (isOpen ? "0" : "3px")};
  display: flex;
`;
const CollapseContainer = styled.div`
  border: 1px solid #ececec;
  border-top: none;
  padding: 20px;
  border-bottom-right-radius: 3px;
  border-bottom-left-radius: 3px;
  margin-bottom: 5px;
`;

export const PARTITIONS_NAME_QUERY = gql`
  query PartitionsNameQuery($partitionSetName: String!, $repositorySelector: RepositorySelector!) {
    partitionSetOrError(
      partitionSetName: $partitionSetName
      repositorySelector: $repositorySelector
    ) {
      ... on PartitionSet {
        partitionsOrError {
          ... on Partitions {
            results {
              name
            }
          }
          ... on PythonError {
            ...PythonErrorFragment
          }
        }
        pipelineName
      }
      ... on PartitionSetNotFoundError {
        message
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
`;

export const LAUNCH_PARTITION_BACKFILL_MUTATION = gql`
  mutation LaunchPartitionBackfill($backfillParams: PartitionBackfillParams!) {
    launchPartitionBackfill(backfillParams: $backfillParams) {
      __typename
      ... on PartitionBackfillSuccess {
        backfillId
      }
      ... on PartitionSetNotFoundError {
        message
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

export const PARTITION_FAILED_SELECTOR_PIPELINE_QUERY = gql`
  query PartitionFailedSelectorPipelineQuery(
    $repositorySelector: RepositorySelector!
    $partitionSetName: String!
  ) {
    partitionSetOrError(
      repositorySelector: $repositorySelector
      partitionSetName: $partitionSetName
    ) {
      ... on PartitionSet {
        partitionsOrError {
          ... on Partitions {
            results {
              name
              runs(limit: 1) {
                runId
                status
              }
            }
          }
        }
      }
    }
  }
`;

export const PARTITION_STEP_SELECTOR_PIPELINE_QUERY = gql`
  query PartitionStepSelectorPipelineQuery(
    $pipelineSelector: PipelineSelector!
    $repositorySelector: RepositorySelector!
    $partitionSetName: String!
  ) {
    pipelineSnapshotOrError(activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
        name
        solidHandles {
          handleID
          solid {
            name
            definition {
              name
            }
            inputs {
              dependsOn {
                solid {
                  name
                }
              }
            }
            outputs {
              dependedBy {
                solid {
                  name
                }
              }
            }
          }
        }
      }
    }
    partitionSetOrError(
      repositorySelector: $repositorySelector
      partitionSetName: $partitionSetName
    ) {
      ... on PartitionSet {
        partitionsOrError {
          ... on Partitions {
            results {
              name
              runs(limit: 1) {
                runId
                status
              }
            }
          }
        }
      }
    }
  }
`;
