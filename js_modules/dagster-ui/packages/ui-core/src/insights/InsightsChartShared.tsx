import {Colors, IconName} from '@dagster-io/ui-components';
import styled from 'styled-components';

import {DatapointType} from './types';

export const iconForDatapointType = (type: DatapointType): IconName => {
  switch (type) {
    case 'asset-group':
      return 'asset_group';
    case 'asset':
      return 'asset';
    case 'deployment':
      return 'code_location';
    default:
      return 'job';
  }
};

export const LoadingStateContainer = styled.div`
  position: absolute;
  top: calc(50% - 50px);
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

export const EmptyStateContainer = styled.div`
  position: absolute;
  top: calc(45% - 50px);
  left: 0;
  right: 0;
  bottom: 0;
`;

export const TooltipCard = styled.div`
  background-color: ${Colors.popoverBackground()};
  border-radius: 6px;
  box-shadow: 0px 2px 12px 0px rgba(0, 0, 0, 0.12);
  cursor: default;
  overflow: hidden;
  user-select: none;
  width: 240px;
`;
