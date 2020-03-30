import * as React from "react";
import styled from "styled-components/macro";
import { Colors, Button, ButtonGroup } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import {
  LogFilter,
  LogLevel,
  LogFilterValue,
  GetFilterProviders
} from "./LogsProvider";
import { ComputeLogLink } from "./ComputeLogModal";
import { IStepState } from "../RunMetadataProvider";
import {
  TokenizingField,
  TokenizingFieldValue,
  SuggestionProvider
} from "../TokenizingField";

interface ILogsToolbarProps {
  steps: string[];
  filter: LogFilter;
  filterStep: string | null;
  filterStepState: IStepState;
  onSetFilter: (filter: LogFilter) => void;
}

const suggestionProvidersFilter = (
  suggestionProviders: SuggestionProvider[],
  values: TokenizingFieldValue[]
) => {
  const tokens: string[] = [];
  for (const { token } of values) {
    if (token) {
      tokens.push(token);
    }
  }

  // If id is set, then no other filters can be set
  if (tokens.includes("id")) {
    return [];
  }

  // Can only have one filter value for pipeline, status, or id
  const limitedTokens = new Set<string>(["id", "pipeline", "status"]);
  const presentLimitedTokens = tokens.filter(token => limitedTokens.has(token));

  return suggestionProviders.filter(
    provider => !presentLimitedTokens.includes(provider.token)
  );
};

export default class LogsToolbar extends React.PureComponent<
  ILogsToolbarProps
> {
  render() {
    const {
      steps,
      filter,
      filterStep,
      filterStepState,
      onSetFilter
    } = this.props;

    return (
      <LogsToolbarContainer>
        <FilterTokenizingField
          values={filter.values}
          onChange={(values: LogFilterValue[]) =>
            onSetFilter({ ...filter, values })
          }
          className={filterStep ? "has-step" : ""}
          suggestionProviders={GetFilterProviders(steps)}
          suggestionProvidersFilter={suggestionProvidersFilter}
          loading={false}
          maxValues={1}
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
            View Raw Step Output
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

const FilterTokenizingField = styled(TokenizingField)`
  flex: 2;
  height: 20px;
  min-width: 100px;
  &.has-step {
    box-shadow: 0 0 0 2px ${Colors.GOLD3};
    border-radius: 3px;
  }
  &.bp3-tag-input {
    min-height: 26px;
  }
  &.bp3-tag-input .bp3-tag-input-values {
    height: 23px;
    margin-top: 3px;
  }
`;
