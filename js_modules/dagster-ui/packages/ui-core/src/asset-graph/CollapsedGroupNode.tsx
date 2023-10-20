import {Box, ButtonLink, Colors, FontFamily, Icon} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {withMiddleTruncation} from '../app/Util';

import {AssetDescription, NameTooltipStyle} from './AssetNode';

export const GroupNodeNameAndRepo: React.FC<{
  minimal: boolean;
  group: {
    groupName: string;
    repositoryName: string;
    repositoryLocationName: string;
  };
}> = ({group, minimal}) => {
  const name = `${group.groupName} `;
  const location = `${group.repositoryName}@${group.repositoryLocationName}`;
  if (minimal) {
    return (
      <Box padding={{vertical: 2}} flex={{direction: 'column'}}>
        <Box
          data-tooltip={name}
          data-tooltip-style={NameTooltipStyle}
          style={{
            overflow: 'hidden',
            textAlign: 'center',
            textOverflow: 'ellipsis',
            fontFamily: FontFamily.monospace,
            fontSize: 30,
            lineHeight: '30px',
            fontWeight: 600,
          }}
        >
          {withMiddleTruncation(name, {maxLength: 18})}
        </Box>
        <Box style={{fontFamily: FontFamily.monospace, textAlign: 'center', fontSize: 20}}>
          {withMiddleTruncation(location, {maxLength: 26})}
        </Box>
      </Box>
    );
  }
  return (
    <>
      <Box style={{padding: '6px 8px'}} flex={{direction: 'row', gap: 4}}>
        <span style={{marginTop: 1}}>
          <Icon name="asset_group" />
        </span>
        <div
          data-tooltip={name}
          data-tooltip-style={NameTooltipStyle}
          style={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            fontWeight: 600,
            fontFamily: FontFamily.monospace,
          }}
        >
          {withMiddleTruncation(name, {maxLength: 35})}
        </div>
        <div style={{flex: 1}} />
      </Box>
      <Box
        style={{padding: '6px 8px', fontFamily: FontFamily.monospace}}
        flex={{direction: 'column', gap: 4}}
        border="top"
      >
        {withMiddleTruncation(location, {maxLength: 38})}
      </Box>
    </>
  );
};
export const CollapsedGroupNode: React.FC<{
  minimal: boolean;
  onExpand: () => void;
  group: {
    assetCount: number;
    groupName: string;
    repositoryName: string;
    repositoryLocationName: string;
  };
}> = ({group, minimal, onExpand}) => {
  return (
    <CollapsedGroupNodeContainer>
      <CollapsedGroupNodeBox $minimal={minimal}>
        <GroupNodeNameAndRepo group={group} minimal={minimal} />
        <Box
          style={{padding: '6px 8px'}}
          flex={{direction: 'row', justifyContent: 'space-between', gap: 4}}
          border="top"
        >
          <ButtonLink onClick={onExpand}>Expand</ButtonLink>
          <AssetDescription $color={Colors.Gray400}>{group.assetCount} assets</AssetDescription>
        </Box>
      </CollapsedGroupNodeBox>
    </CollapsedGroupNodeContainer>
  );
};

const CollapsedGroupNodeContainer = styled.div`
  user-select: none;
  cursor: default;
  padding: 4px;
`;

const CollapsedGroupNodeBox = styled.div<{$minimal: boolean}>`
  border: ${(p) => (p.$minimal ? '4px' : '2px')} solid ${Colors.Gray200};
  background: ${Colors.White};
  border-radius: 8px;
  position: relative;
`;
