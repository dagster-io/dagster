import {
  Box,
  FontFamily,
  Icon,
  colorBackgroundLight,
  colorBackgroundLightHover,
  colorBackgroundLighter,
  colorLineageGroupNodeBorder,
  colorTextLight,
  colorTextLighter,
} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {withMiddleTruncation} from '../app/Util';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';

import {AssetDescription, NameTooltipCSS} from './AssetNode';
import {GroupLayout} from './layout';

export const GroupNodeNameAndRepo = ({group, minimal}: {minimal: boolean; group: GroupLayout}) => {
  const name = `${group.groupName} `;
  const location = repoAddressAsHumanString({
    name: group.repositoryName,
    location: group.repositoryLocationName,
  });

  if (minimal) {
    return (
      <Box style={{flex: 1, fontFamily: FontFamily.monospace}}>
        <div
          data-tooltip={name}
          data-tooltip-style={GroupNameTooltipStyle}
          style={{fontSize: 30, fontWeight: 600, lineHeight: '30px'}}
        >
          {withMiddleTruncation(name, {maxLength: 14})}
        </div>
      </Box>
    );
  }
  return (
    <Box style={{flex: 1, fontFamily: FontFamily.monospace}}>
      <Box flex={{direction: 'row', gap: 4}}>
        <div
          data-tooltip={name}
          data-tooltip-style={GroupNameTooltipStyle}
          style={{fontSize: 20, fontWeight: 600, lineHeight: '1.1em'}}
        >
          {withMiddleTruncation(name, {maxLength: 22})}
        </div>
      </Box>
      <Box style={{lineHeight: '1em', color: colorTextLight()}}>
        {withMiddleTruncation(location, {maxLength: 31})}
      </Box>
    </Box>
  );
};

export const CollapsedGroupNode = ({
  group,
  minimal,
  onExpand,
}: {
  minimal: boolean;
  onExpand: () => void;
  group: GroupLayout & {assetCount: number};
}) => {
  return (
    <CollapsedGroupNodeContainer
      onClick={(e) => {
        onExpand();
        e.stopPropagation();
      }}
    >
      <CollapsedGroupNodeBox $minimal={minimal}>
        <Box padding={{vertical: 8, left: 12, right: 8}} flex={{}}>
          <GroupNodeNameAndRepo group={group} minimal={minimal} />
          <Box padding={{vertical: 4}}>
            <Icon name="unfold_more" />
          </Box>
        </Box>
        {!minimal && (
          <Box padding={{horizontal: 12, bottom: 4}}>
            <AssetDescription $color={colorTextLighter()}>
              {group.assetCount} {group.assetCount === 1 ? 'asset' : 'assets'}
            </AssetDescription>
          </Box>
        )}
      </CollapsedGroupNodeBox>
      <GroupStackLine style={{width: '94%', marginLeft: '3%'}} />
      <GroupStackLine style={{width: '88%', marginLeft: '6%'}} />
    </CollapsedGroupNodeContainer>
  );
};

export const GroupNameTooltipStyle = JSON.stringify({
  ...NameTooltipCSS,
  background: colorBackgroundLighter(),
  border: `none`,
  borderRadius: '4px',
});

const GroupStackLine = styled.div`
  background: transparent;
  border-top: 2px solid ${colorLineageGroupNodeBorder()};
  border-radius: 2px;
`;

const CollapsedGroupNodeBox = styled.div<{$minimal: boolean}>`
  border: ${(p) => (p.$minimal ? '4px' : '2px')} solid ${colorLineageGroupNodeBorder()};
  background: ${colorBackgroundLight()};
  border-radius: 8px;
  position: relative;
  margin-top: 8px;
`;

const CollapsedGroupNodeContainer = styled.div`
  user-select: none;
  padding: 4px;
  transition:
    transform linear 200ms,
    gap linear 200ms;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;

  &:hover {
    transform: scale(1.03);
    gap: 3px;
    ${CollapsedGroupNodeBox} {
      transition: background linear 200ms;
      background: ${colorBackgroundLightHover()};
    }
  }
`;
