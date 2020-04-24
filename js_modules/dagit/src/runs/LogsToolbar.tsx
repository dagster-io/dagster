import * as React from "react";
import styled from "styled-components/macro";
import {
  Spinner,
  Intent,
  Colors,
  Button,
  ButtonGroup,
  InputGroup,
  Icon
} from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { ILogFilter, LogLevel } from "./LogsProvider";
import { ComputeLogLink } from "./ComputeLogModal";
import { IStepState } from "../RunMetadataProvider";

interface ILogsToolbarProps {
  filter: ILogFilter;
  filterStep: string | null;
  filterStepState: IStepState;
  onSetFilter: (filter: ILogFilter) => void;
  showSpinner: boolean;
}

const FilterSpinner = <Spinner intent={Intent.NONE} size={16} />;

export default class LogsToolbar extends React.PureComponent<
  ILogsToolbarProps
> {
  render() {
    const {
      filter,
      filterStep,
      filterStepState,
      onSetFilter,
      showSpinner
    } = this.props;

    return (
      <LogsToolbarContainer>
        <FilterInputGroup
          leftIcon="filter"
          placeholder="Filter logs..."
          className={filterStep ? "has-step" : ""}
          small={true}
          value={filter.text}
          spellCheck={false}
          rightElement={
            showSpinner ? (
              FilterSpinner
            ) : filter.text.length ? (
              <Icon
                color={Colors.GRAY1}
                icon={IconNames.SMALL_CROSS}
                style={{ padding: 4 }}
                onClick={() => onSetFilter({ ...filter, text: "" })}
              />
            ) : (
              undefined
            )
          }
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            onSetFilter({ ...filter, text: e.target.value })
          }
        />
        <LogsToolbarDivider />
        <ButtonGroup>
          {Object.keys(LogLevel).map(level => (
            <Button
              key={level}
              text={level.toLowerCase()}
              small={true}
              style={{ textTransform: "capitalize" }}
              active={filter.levels[level]}
              onClick={() =>
                onSetFilter({
                  ...filter,
                  levels: {
                    ...filter.levels,
                    [level]: !filter.levels[level]
                  }
                })
              }
            />
          ))}
        </ButtonGroup>
        {filterStep && <LogsToolbarDivider />}
        {filterStep && (
          <ComputeLogLink stepKey={filterStep} runState={filterStepState}>
            <Button icon={"console"} small>
              View Raw Step Output
            </Button>
          </ComputeLogLink>
        )}
        <div style={{ minWidth: 15, flex: 1 }} />
        <Button
          text={"Clear"}
          small={true}
          icon={IconNames.ERASER}
          onClick={() => onSetFilter({ ...filter, since: Date.now() })}
        />
        {this.props.children}
      </LogsToolbarContainer>
    );
  }
}

const LogsToolbarContainer = styled.div`
  display: flex;
  flex-direction: row;
  background: ${Colors.WHITE};
  height: 40px;
  align-items: center;
  padding: 5px 15px;
  border-bottom: 1px solid ${Colors.GRAY4};
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.07);
  z-index: 2;
`;

const LogsToolbarDivider = styled.div`
  display: inline-block;
  width: 1px;
  height: 30px;
  margin: 0 15px;
  border-right: 1px solid ${Colors.LIGHT_GRAY3};
`;

const FilterInputGroup = styled(InputGroup)`
  flex: 2;
  max-width: 375px;
  min-width: 100px;
  & input {
    padding-right: 22px !important;
  }
  &.has-step {
    box-shadow: 0 0 0 2px ${Colors.GOLD3};
    border-radius: 3px;
  }
`;
