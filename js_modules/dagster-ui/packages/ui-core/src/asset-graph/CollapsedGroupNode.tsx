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
            fontFamily: FontFamily.default,
            fontSize: 24,
            lineHeight: '32px',
            fontWeight: 500,
          }}
        >
          {withMiddleTruncation(name, {maxLength: 16})}
        </Box>
      </Box>
    );
  }
  return (
    <>
      <Box style={{padding: '6px 8px'}} flex={{direction: 'row', gap: 8}}>
        <div
          data-tooltip={name}
          data-tooltip-style={NameTooltipStyle}
          style={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            fontWeight: 500,
            fontFamily: FontFamily.default,
            fontSize: 20,
          }}
        >
          {withMiddleTruncation(name, {maxLength: 19})}
        </div>
        <div style={{flex: 1}} />
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
      <CollapsedGroupNodeBox $minimal={minimal} onClick={onExpand}>
        <Box
          style={{paddingRight: '6px'}}

          flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
        >
          <GroupNodeNameAndRepo group={group} minimal={minimal} />
          <Icon size={24} color={Colors.Gray500} name="unfold_more" />
        </Box>
        <Box
          style={{padding: '6px 8px'}}
          flex={{direction: 'row', justifyContent: 'space-between', gap: 4}}
        >
          <p style={{
            color: Colors.Gray600,
            margin: '0px',
            fontSize: '16px',
          }}>
            {group.assetCount} {group.assetCount === 1 ? "asset" : "assets"}
          </p>
        </Box>
      </CollapsedGroupNodeBox>
    </CollapsedGroupNodeContainer>
  );
};

const CollapsedGroupNodeContainer = styled.div`
  user-select: none;
  padding: 3px;
`;

const CollapsedGroupNodeBox = styled.div<{$minimal: boolean}>`
  border: ${(p) => (p.$minimal ? '4px' : '2px')} solid ${Colors.KeylineGray};
  background: ${Colors.Gray50};
  border-radius: 12px;
  padding: 6px;
  cursor: pointer;
  position: relative;
  transition: all 200ms ease-in-out;
  :hover {
    background: ${Colors.Gray100};
    scale: 1.02;
    :before{
      bottom: -8px;
    }
    :after{
      bottom: -14px;
    }
  }
  :before{
    content: "";
    transition: all 200ms ease-in-out;
    position: absolute;
    bottom: -6px;
    left: 0;
    right: 0;
    width: 94%;
    margin: 0 auto;
    height: 2px;
    background: ${Colors.KeylineGray};
  }
  :after{
    content: "";
    transition: all 200ms ease-in-out;
    position: absolute;
    bottom: -10px;
    left: 0;
    right: 0;
    width: 90%;
    margin: 0 auto;
    height: 2px;
    background: ${Colors.KeylineGray};
  }
`;
