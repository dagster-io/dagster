import {Colors, Tooltip, FontFamily} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

export const LegacyPipelineTag = () => (
  <Tooltip content="Legacy pipeline" placement="top">
    <LegacyTag>Legacy</LegacyTag>
  </Tooltip>
);

const LegacyTag = styled.div`
  background: ${Colors.Gray10};
  color: ${Colors.Gray600};
  font-family: ${FontFamily.default};
  font-size: 14px;
  border-radius: 7px;
  text-overflow: ellipsis;
  overflow: hidden;
  padding: 5px;
  user-select: none;
  margin: -3px 0;
  font-size: 11px;
`;
