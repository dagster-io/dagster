import {capitalize} from 'lodash';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
import {NonIdealState} from '../ui/NonIdealState';

export const LargeDAGNotice = ({nodeType}: {nodeType: 'op' | 'asset'}) => (
  <LargeDAGContainer>
    <LargeDAGInstructionBox>
      <p>
        This is a large DAG that may be difficult to visualize. Type <code>*</code> in the subset
        box below to render the entire thing, or type a {nodeType} name and use:
      </p>
      <ul style={{marginBottom: 0}}>
        <li>
          <code>+</code> to expand a single layer before or after the {nodeType}.
        </li>
        <li>
          <code>*</code> to expand recursively before or after the {nodeType}.
        </li>
        <li>
          <code>AND</code> to render another disconnected fragment.
        </li>
      </ul>
    </LargeDAGInstructionBox>
    <IconWIP name="arrow_downward" size={24} />
  </LargeDAGContainer>
);

export const EmptyDAGNotice: React.FC<{isGraph: boolean; nodeType: 'asset' | 'op'}> = ({
  isGraph,
  nodeType,
}) => {
  return (
    <NonIdealState
      icon="no-results"
      title={isGraph ? 'Empty graph' : 'Empty pipeline'}
      description={
        <>
          <div>This {isGraph ? 'graph' : 'pipeline'} is empty.</div>
          <div>{capitalize(nodeType)} will appear here when you add them.</div>
        </>
      }
    />
  );
};

const LargeDAGContainer = styled.div`
  width: 50vw;
  position: absolute;
  transform: translateX(-50%);
  left: 50%;
  bottom: 60px;
  z-index: 2;
  max-width: 600px;
  display: flex;
  flex-direction: column;
  align-items: center;
  .bp3-icon {
    color: ${ColorsWIP.Gray200};
  }
`;

const LargeDAGInstructionBox = styled.div`
  padding: 15px 20px;
  border: 1px solid #fff5c3;
  margin-bottom: 20px;
  color: ${ColorsWIP.Gray800};
  background: #fffbe5;
  text-align: left;
  line-height: 1.4rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  code {
    background: #f8ebad;
    font-weight: 500;
    padding: 0 4px;
  }
`;
