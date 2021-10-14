import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {usePermissions} from '../app/Permissions';
import {Box} from '../ui/Box';
import {Checkbox} from '../ui/Checkbox';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP, IconWrapper} from '../ui/Icon';
import {Spinner} from '../ui/Spinner';
import {Table} from '../ui/Table';
import {Caption} from '../ui/Text';
import {Tooltip} from '../ui/Tooltip';
import {FontFamily} from '../ui/styles';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {ReloadRepositoryLocationButton} from './ReloadRepositoryLocationButton';

export type RepoDetails = {
  repoAddress: RepoAddress;
  metadata: {key: string; value: string}[];
};

interface Props {
  onBrowse: () => void;
  onToggle: (repoDetails: RepoDetails) => void;
  options: RepoDetails[];
  selected: Set<RepoDetails>;
}

export const RepoSelector: React.FC<Props> = (props) => {
  const {onBrowse, onToggle, options, selected} = props;
  const {canReloadRepositoryLocation} = usePermissions();

  return (
    <Table>
      <tbody>
        {options.map((option) => {
          const {repoAddress, metadata} = option;
          const addressString = repoAddressAsString(repoAddress);
          const checked = selected.has(option);
          return (
            <tr key={addressString}>
              <td>
                <Checkbox
                  checked={checked}
                  onChange={(e) => {
                    if (e.target instanceof HTMLInputElement) {
                      onToggle(option);
                    }
                  }}
                  id={`switch-${addressString}`}
                />
              </td>
              <td>
                <RepoLabel htmlFor={`switch-${addressString}`}>
                  <Group direction="column" spacing={4}>
                    <Box flex={{direction: 'row'}} title={addressString}>
                      <RepoName>{repoAddress.name}</RepoName>
                      <RepoLocation>{`@${repoAddress.location}`}</RepoLocation>
                    </Box>
                    <Group direction="column" spacing={2}>
                      {metadata.map(({key, value}) => (
                        <Caption
                          style={{color: ColorsWIP.Gray400, fontFamily: FontFamily.monospace}}
                          key={key}
                        >{`${key}: ${value}`}</Caption>
                      ))}
                    </Group>
                  </Group>
                </RepoLabel>
              </td>
              <td>
                <Link to={workspacePathFromAddress(repoAddress)} onClick={() => onBrowse()}>
                  Browse
                </Link>
              </td>
              {canReloadRepositoryLocation ? (
                <td>
                  <ReloadButton repoAddress={repoAddress} />
                </td>
              ) : null}
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
};

const RepoLabel = styled.label`
  cursor: pointer;
  display: block;
  font-weight: 500;
  line-height: 1;
  overflow: hidden;
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
  color: ${ColorsWIP.Gray800};
`;

const RepoLocation = styled.div`
  color: ${ColorsWIP.Gray700};
  font-family: ${FontFamily.monospace};
`;

const ReloadButton: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  return (
    <ReloadRepositoryLocationButton location={repoAddress.location}>
      {({tryReload, reloading}) => (
        <Tooltip
          placement="right"
          content={
            reloading ? (
              'Reloading…'
            ) : (
              <>
                Reload <strong>{repoAddress.location}</strong>
              </>
            )
          }
        >
          <ReloadButtonInner onClick={tryReload}>
            {reloading ? (
              <Spinner purpose="body-text" />
            ) : (
              <IconWIP name="refresh" color={ColorsWIP.Gray200} />
            )}
          </ReloadButtonInner>
        </Tooltip>
      )}
    </ReloadRepositoryLocationButton>
  );
};

const ReloadButtonInner = styled.button`
  background: transparent;
  border: 0;
  cursor: pointer;
  padding: 2px;
  outline: none;

  ${IconWrapper} {
    background-color: ${ColorsWIP.Gray600};
    transition: background-color 100ms;
  }

  :hover ${IconWrapper} {
    background-color: ${ColorsWIP.Gray800};
  }

  :focus ${IconWrapper} {
    background-color: ${ColorsWIP.Link};
  }
`;
