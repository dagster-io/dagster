import {Colors, Icon} from '@blueprintjs/core';
import {Popover2 as Popover} from '@blueprintjs/popover2';
import memoize from 'lodash/memoize';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';
import {MetadataTable} from 'src/ui/MetadataTable';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

const colors = [
  Colors.BLUE3,
  Colors.COBALT3,
  Colors.FOREST3,
  Colors.GOLD3,
  Colors.GREEN3,
  Colors.INDIGO3,
  Colors.LIME3,
  Colors.ORANGE3,
  Colors.ROSE3,
  Colors.SEPIA3,
  Colors.TURQUOISE3,
  Colors.VERMILION3,
  Colors.VIOLET3,
];

const colorForString = memoize((s: string) => {
  const index =
    Math.abs(
      s.split('').reduce((a, b) => {
        a = (a << 5) - a + b.charCodeAt(0);
        return a & a;
      }, 0),
    ) % colors.length;
  return colors[index];
});

type RepoStatus = 'on' | 'off';

interface Props {
  onClick?: (e: React.MouseEvent) => void;
  repoAddress: RepoAddress;
  showTooltip: boolean;
  status: RepoStatus;
}

export const RepoBlob: React.FC<Props> = (props) => {
  const {repoAddress, showTooltip, status, onClick} = props;
  const addressString = repoAddressAsString(repoAddress);
  return (
    <Popover
      interactionKind="hover"
      placement="top"
      popoverClassName="bp3-dark"
      content={
        showTooltip ? (
          <div>
            <Box padding={{vertical: 12, horizontal: 16}} background={Colors.DARK_GRAY2}>
              <MetadataTable
                rows={[
                  {key: 'Name', value: repoAddress.name},
                  {key: 'Location', value: repoAddress.location},
                ]}
              />
            </Box>
            <Box
              flex={{direction: 'row', justifyContent: 'space-between'}}
              padding={{horizontal: 16, vertical: 12}}
            >
              <Link to={workspacePathFromAddress(repoAddress)}>Browse</Link>
              <ButtonLink color={Colors.LIGHT_GRAY2} underline="hover">
                <Group direction="row" spacing={8} alignItems="center">
                  <Icon
                    icon="refresh"
                    iconSize={9}
                    color={Colors.LIGHT_GRAY2}
                    style={{position: 'relative', top: '-3px'}}
                  />
                  <div>Reload</div>
                </Group>
              </ButtonLink>
            </Box>
          </div>
        ) : undefined
      }
    >
      <Blob $color={colorForString(addressString)} $status={status} onClick={onClick}>
        {addressString.slice(0, 1)}
      </Blob>
    </Popover>
  );
};

interface BlobProps {
  $color: string;
  $status: RepoStatus;
}

const backgroundColor = ({$color, $status}: BlobProps) =>
  $status === 'off' ? 'transparent' : $color;

const textColor = ({$status}: BlobProps) => ($status === 'off' ? Colors.GRAY1 : Colors.WHITE);

const Blob = styled.button<BlobProps>`
  align-items: center;
  background-color: ${backgroundColor};
  border: 1px solid ${({$status}) => ($status === 'off' ? Colors.GRAY1 : 'transparent')};
  border-radius: 10px;
  color: ${textColor};
  cursor: pointer;
  display: flex;
  font-size: 13px;
  height: 20px;
  justify-content: center;
  outline: none;
  text-transform: uppercase;
  transition: background 50ms linear, color 50ms linear;
  user-select: none;
  width: 20px;

  :focus,
  :active {
    outline: none;
  }
`;
