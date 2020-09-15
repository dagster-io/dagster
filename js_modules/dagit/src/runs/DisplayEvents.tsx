import * as React from 'react';
import styled from 'styled-components/macro';
import {Colors, Tag, Intent, Divider} from '@blueprintjs/core';
import {DisplayEvent} from './DisplayEvent';
import {
  IExpectationResult,
  IExpectationResultStatus,
  IMaterialization,
} from '../RunMetadataProvider';

interface IDisplayEventsProps {
  expectationResults: IExpectationResult[];
  materializations: IMaterialization[];
}

interface IDisplayEventsState {
  expectationsExpanded: boolean;
  materializationsExpanded: boolean;
}

export class DisplayEvents extends React.Component<IDisplayEventsProps, IDisplayEventsState> {
  state = {
    expectationsExpanded: false,
    materializationsExpanded: true,
  };

  render() {
    const {expectationsExpanded, materializationsExpanded} = this.state;
    const {expectationResults, materializations} = this.props;

    const nPassed = expectationResults.filter((e) => e.status === IExpectationResultStatus.PASSED)
      .length;
    const nFailed = expectationResults.filter((e) => e.status === IExpectationResultStatus.FAILED)
      .length;

    return (
      <DisplayEventsContainer>
        {expectationResults.length > 0 && (
          <div>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
              }}
            >
              <DisclosureTriangle
                expanded={expectationsExpanded}
                onClick={() => this.setState({expectationsExpanded: !expectationsExpanded})}
              />
              <div style={{width: 4}} />
              <span style={{fontWeight: 500}}> Expectations</span>&nbsp;
              <ExpectationsTag intent={nPassed ? Intent.SUCCESS : Intent.NONE}>
                {nPassed} passed
              </ExpectationsTag>
              &nbsp;
              <ExpectationsTag intent={nFailed ? Intent.DANGER : Intent.NONE}>
                {nFailed} failed
              </ExpectationsTag>
            </div>
            {expectationsExpanded && (
              <div>
                {expectationResults.map((e, idx) => (
                  <DisplayEvent event={e} key={`${idx}`} />
                ))}
              </div>
            )}
          </div>
        )}
        {expectationResults.length > 0 && materializations.length > 0 && <Divider />}
        {materializations.length > 0 && (
          <div>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
              }}
            >
              <DisclosureTriangle
                expanded={materializationsExpanded}
                onClick={() =>
                  this.setState({
                    materializationsExpanded: !materializationsExpanded,
                  })
                }
              />
              <div style={{width: 4}} />
              <span style={{fontWeight: 500}}> Materializations</span>&nbsp;
              <ExpectationsTag intent={Intent.NONE}>
                {materializations.length} materialized values
              </ExpectationsTag>
            </div>
            {materializationsExpanded &&
              materializations.map((e, idx) => <DisplayEvent event={e} key={`${idx}`} />)}
          </div>
        )}
      </DisplayEventsContainer>
    );
  }
}

const DisplayEventsContainer = styled.div`
  color: ${Colors.BLACK};
  border-top: 1px solid rgba(0, 0, 0, 0.15);
  margin-top: 4px;
  padding-left: 16px;
  padding-top: 6px;
`;

const ExpectationsTag = styled(Tag)`
  font-size: 10px;
  min-height: 10px;
  min-width: 10px;
  padding-right: 4px;
  padding-left: 4px;
  padding-top: 0;
  padding-bottom: 0;
`;

const DisclosureTriangle = styled.div<{expanded: boolean}>`
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 8px solid rgba(0, 0, 0, 0.5);
  transition: transform 150ms linear;
  transform: ${({expanded}) => (expanded ? 'rotate(0deg)' : 'rotate(-90deg)')};
`;
