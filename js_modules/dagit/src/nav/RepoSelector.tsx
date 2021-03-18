import {Colors, Icon} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {SwitchWithoutLabel} from 'src/ui/SwitchWithoutLabel';
import {Caption} from 'src/ui/Text';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

export type RepoDetails = {
  repoAddress: RepoAddress;
  host: string;
  port: string;
};

interface Props {
  onToggle: (repoDetails: RepoDetails) => void;
  options: RepoDetails[];
  selected: Set<RepoDetails>;
}

export const RepoSelector: React.FC<Props> = (props) => {
  const {onToggle, options, selected} = props;

  return (
    <Group direction="column" spacing={16}>
      {options.map((option) => {
        const {repoAddress, host, port} = option;
        const addressString = repoAddressAsString(repoAddress);
        const checked = selected.has(option);
        return (
          <Box key={addressString} flex={{direction: 'row', alignItems: 'center'}}>
            {options.length > 1 ? (
              <SwitchWithoutLabel
                checked={checked}
                onChange={(e) => {
                  if (e.target instanceof HTMLInputElement) {
                    onToggle(option);
                  }
                }}
                id={`switch-${addressString}`}
                style={{marginRight: '12px'}}
              />
            ) : null}
            <RepoLabel htmlFor={`switch-${addressString}`}>
              <Group direction="column" spacing={4}>
                <Box flex={{direction: 'row'}} title={addressString}>
                  <RepoName>{repoAddress.name}</RepoName>
                  <RepoLocation>{`@${repoAddress.location}`}</RepoLocation>
                </Box>
                <Caption style={{color: Colors.GRAY3}}>{`host: ${host}, port: ${port}`}</Caption>
              </Group>
            </RepoLabel>
            <Box margin={{left: 16}}>
              <BrowseLink to={workspacePathFromAddress(repoAddress)}>Browse</BrowseLink>
            </Box>
            <ReloadButton repoAddress={repoAddress} />
          </Box>
        );
      })}
    </Group>
  );
};

const RepoLabel = styled.label`
  cursor: pointer;
  flex-grow: 1;
  font-size: 14px;
  font-weight: 500;
  line-height: 1;
  overflow: hidden;
  padding: 0;
  position: relative;
  top: 1px;
  transition: filter 50ms linear;
  user-select: none;
  white-space: nowrap;

  :focus,
  :active {
    outline: none;
  }

  :hover {
    filter: opacity(0.8);
  }
`;

const RepoName = styled.div`
  color: ${Colors.LIGHT_GRAY5};
`;

const RepoLocation = styled.div`
  color: ${Colors.GRAY3};
`;

const BrowseLink = styled(Link)`
  && {
    color: ${Colors.GRAY5};
  }

  &&:hover,
  &&:active {
    color: ${Colors.GRAY3};
  }
`;

const ReloadButton: React.FC<{repoAddress: RepoAddress}> = () => {
  return (
    <ReloadButtonInner onClick={() => {}}>
      <Icon icon="refresh" iconSize={14} color={Colors.GRAY5} />
    </ReloadButtonInner>
  );
};

const ReloadButtonInner = styled.button`
  background: transparent;
  border: 0;
  cursor: pointer;
  padding: 4px;
  margin: 0 0 0 12px;

  :hover .bp3-icon svg {
    fill: ${Colors.GRAY3};
  }
`;
