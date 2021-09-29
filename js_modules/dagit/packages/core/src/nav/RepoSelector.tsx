import {Checkbox} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {usePermissions} from '../app/Permissions';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP, IconWrapper} from '../ui/Icon';
import {Spinner} from '../ui/Spinner';
import {Caption} from '../ui/Text';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {ReloadRepositoryLocationButton} from './ReloadRepositoryLocationButton';

export type RepoDetails = {
  repoAddress: RepoAddress;
  metadata: {key: string; value: string}[];
};

interface Props {
  onToggle: (repoDetails: RepoDetails) => void;
  options: RepoDetails[];
  selected: Set<RepoDetails>;
}

export const RepoSelector: React.FC<Props> = (props) => {
  const {onToggle, options, selected} = props;
  const {canReloadRepositoryLocation} = usePermissions();

  return (
    <Group direction="column" spacing={16}>
      {options.map((option) => {
        const {repoAddress, metadata} = option;
        const addressString = repoAddressAsString(repoAddress);
        const checked = selected.has(option);
        return (
          <Box key={addressString} flex={{direction: 'row', alignItems: 'flex-start'}}>
            {options.length > 1 ? (
              <Checkbox
                checked={checked}
                onChange={(e) => {
                  if (e.target instanceof HTMLInputElement) {
                    onToggle(option);
                  }
                }}
                id={`switch-${addressString}`}
                style={{marginRight: '4px'}}
              />
            ) : null}
            <RepoLabel htmlFor={`switch-${addressString}`}>
              <Group direction="column" spacing={4}>
                <Box flex={{direction: 'row'}} title={addressString}>
                  <RepoName>{repoAddress.name}</RepoName>
                  <RepoLocation>{`@${repoAddress.location}`}</RepoLocation>
                </Box>
                <Group direction="column" spacing={2}>
                  {metadata.map(({key, value}) => (
                    <Caption
                      style={{color: ColorsWIP.Gray400}}
                      key={key}
                    >{`${key}: ${value}`}</Caption>
                  ))}
                </Group>
              </Group>
            </RepoLabel>
            <Box margin={{left: 16, top: 1}} style={{lineHeight: 1}}>
              <BrowseLink to={workspacePathFromAddress(repoAddress)}>Browse</BrowseLink>
            </Box>
            {canReloadRepositoryLocation ? <ReloadButton repoAddress={repoAddress} /> : null}
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
  color: ${ColorsWIP.Gray50};
`;

const RepoLocation = styled.div`
  color: ${ColorsWIP.Gray400};
`;

const BrowseLink = styled(Link)`
  line-height: 1;

  && {
    color: ${ColorsWIP.Gray200};
  }

  &&:hover,
  &&:active {
    color: ${ColorsWIP.Gray400};
  }
`;

const ReloadButton: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  return (
    <ReloadRepositoryLocationButton location={repoAddress.location}>
      {({tryReload, reloading}) => (
        <ReloadButtonInner onClick={tryReload}>
          {reloading ? (
            <Spinner purpose="body-text" />
          ) : (
            <IconWIP name="refresh" color={ColorsWIP.Gray200} />
          )}
        </ReloadButtonInner>
      )}
    </ReloadRepositoryLocationButton>
  );
};

const ReloadButtonInner = styled.button`
  background: transparent;
  border: 0;
  cursor: pointer;
  padding: 2px;
  margin: -2px 0 0 8px;
  outline: none;

  :hover ${IconWrapper} {
    color: ${ColorsWIP.Gray500};
  }

  :focus ${IconWrapper} {
    color: ${ColorsWIP.Gray100};
  }
`;
