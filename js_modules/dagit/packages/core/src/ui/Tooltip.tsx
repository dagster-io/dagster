import {Tooltip2, Tooltip2Props} from '@blueprintjs/popover2';
import deepmerge from 'deepmerge';
import React from 'react';
import {createGlobalStyle} from 'styled-components/macro';

import {ColorsWIP} from './Colors';
import {FontFamily} from './styles';

export const GlobalTooltipStyle = createGlobalStyle`
  .dagit-tooltip .bp3-popover2-content {
      background: ${ColorsWIP.Gray900};
      font-family: ${FontFamily.default};
      font-size: 12px;
      line-height: 16px;
      color: ${ColorsWIP.Gray50};
      padding: 8px 16px;
  }
`;

export const Tooltip: React.FC<Tooltip2Props> = (props) => (
  <Tooltip2
    {...props}
    minimal
    popoverClassName={`dagit-tooltip ${props.popoverClassName}`}
    modifiers={deepmerge(
      {offset: {enabled: true, options: {offset: [0, 8]}}},
      props.modifiers || {},
    )}
  />
);
