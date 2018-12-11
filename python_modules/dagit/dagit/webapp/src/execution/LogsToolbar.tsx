import * as React from "react";
import styled from "styled-components";
import { Colors, Button, ButtonGroup, InputGroup } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { ILogFilter, LogLevel } from "./LogsFilterProvider";

interface ILogsToolbarProps {
  filter: ILogFilter;
  onSetFilter: (filter: ILogFilter) => void;
}

export default class LogsToolbar extends React.Component<ILogsToolbarProps> {
  render() {
    const { filter, onSetFilter } = this.props;
    return (
      <LogsToolbarContainer>
        <FilterInputGroup
          leftIcon="filter"
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            onSetFilter({ ...filter, text: e.target.value })
          }
          placeholder="Filter logs..."
          // rightElement={maybeSpinner}
          small={true}
          value={filter.text}
        />
        <LogsToolbarDivider />
        <ButtonGroup>
          {Object.keys(LogLevel).map(level => (
            <Button
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
        <div style={{ minWidth: 15, flex: 1 }} />
        <Button
          text={"Clear"}
          small={true}
          icon={IconNames.ERASER}
          onClick={() => this.setState({ clearedAtTimestamp: Date.now() })}
        />
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
  max-width: 275px;
  min-width: 100px;
`;
