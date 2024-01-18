import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {
  Box,
  Caption,
  Checkbox,
  Icon,
  IconWrapper,
  Spinner,
  Table,
  Tooltip,
  colorAccentGray,
  colorAccentGrayHover,
  colorLinkDefault,
  colorTextDisabled,
  colorTextLight,
  colorTextLighter,
} from '@dagster-io/ui-components';

import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';
import {
  NO_RELOAD_PERMISSION_TEXT,
  ReloadRepositoryLocationButton,
} from './ReloadRepositoryLocationButton';

export interface RepoSelectorOption {
  repositoryLocation: {name: string};
  repository: {
    name: string;
    displayMetadata: {
      key: string;
      value: string;
    }[];
  };
}

interface Props {
  onBrowse: () => void;
  onToggle: (repoAddresses: RepoAddress[]) => void;
  options: RepoSelectorOption[];
  selected: RepoSelectorOption[];
}

export const RepoSelector = (props: Props) => {
  const {onBrowse, onToggle, options, selected} = props;

  const optionCount = options.length;
  const selectedCount = selected.length;

  const onToggleAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    const {checked} = e.target;
    const reposToToggle = options
      .filter((option) => (checked ? !selected.includes(option) : selected.includes(option)))
      .map((option) => buildRepoAddress(option.repository.name, option.repositoryLocation.name));
    onToggle(reposToToggle);
  };

  return (
    <div>
      <Box padding={{vertical: 8, horizontal: 24}} flex={{alignItems: 'center', gap: 12}}>
        <Checkbox
          checked={selectedCount > 0}
          indeterminate={!!(selectedCount && optionCount !== selectedCount)}
          onChange={onToggleAll}
        />
        {`${selected.length} of ${options.length} selected`}
      </Box>
      <Table>
        <tbody>
          {options.map((option) => {
            const checked = selected.includes(option);
            const repoAddress = {
              location: option.repositoryLocation.name,
              name: option.repository.name,
            };
            const addressString = repoAddressAsHumanString(repoAddress);
            return (
              <tr key={addressString}>
                <td>
                  <Checkbox
                    checked={checked}
                    onChange={(e) => {
                      if (e.target instanceof HTMLInputElement) {
                        onToggle([repoAddress]);
                      }
                    }}
                    id={`switch-${addressString}`}
                  />
                </td>
                <td>
                  <RepoLabel htmlFor={`switch-${addressString}`}>
                    <Box flex={{direction: 'column', gap: 4}}>
                      <RepoLocation>{addressString}</RepoLocation>
                      <Box flex={{direction: 'column', gap: 2}}>
                        {option.repository.displayMetadata.map(({key, value}) => (
                          <Caption
                            style={{color: colorTextLighter()}}
                            key={key}
                          >{`${key}: ${value}`}</Caption>
                        ))}
                      </Box>
                    </Box>
                  </RepoLabel>
                </td>
                <td>
                  <Link to={workspacePathFromAddress(repoAddress)} onClick={() => onBrowse()}>
                    Browse
                  </Link>
                </td>
                <td>
                  <ReloadButton repoAddress={repoAddress} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    </div>
  );
};

const RepoLabel = styled.label`
  cursor: pointer;
  display: block;
  font-weight: 500;
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

const RepoLocation = styled.div`
  color: ${colorTextLight()};
`;

const ReloadButton = ({repoAddress}: {repoAddress: RepoAddress}) => {
  return (
    <ReloadRepositoryLocationButton
      location={repoAddress.location}
      ChildComponent={({codeLocation, tryReload, reloading, hasReloadPermission}) => {
        const tooltipContent = () => {
          if (!hasReloadPermission) {
            return NO_RELOAD_PERMISSION_TEXT;
          }
          return reloading ? (
            'Reloading…'
          ) : (
            <>
              Reload <strong>{codeLocation}</strong>
            </>
          );
        };

        return (
          <Tooltip placement="right" content={tooltipContent()} useDisabledButtonTooltipFix>
            <ReloadButtonInner disabled={!hasReloadPermission} onClick={tryReload}>
              {reloading ? (
                <Spinner purpose="body-text" />
              ) : (
                <Icon
                  name="refresh"
                  color={hasReloadPermission ? colorAccentGray() : colorAccentGrayHover()}
                />
              )}
            </ReloadButtonInner>
          </Tooltip>
        );
      }}
    />
  );
};

const ReloadButtonInner = styled.button`
  background: transparent;
  border: 0;
  cursor: pointer;
  padding: 8px;
  margin: -6px;
  outline: none;

  :disabled {
    cursor: default;
  }

  :disabled ${IconWrapper} {
    background-color: ${colorTextDisabled};
    transition: background-color 100ms;
  }

  ${IconWrapper} {
    background-color: ${colorTextLight()};
    transition: background-color 100ms;
  }

  :hover:not(:disabled) ${IconWrapper} {
    background-color: ${colorTextLighter()};
  }

  :focus ${IconWrapper} {
    background-color: ${colorLinkDefault()};
  }
`;
