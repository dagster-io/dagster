import {
  Box,
  Button,
  DialogFooter,
  DialogHeader,
  Dialog,
  Group,
  Icon,
  IconWrapper,
  Spinner,
  Tooltip,
  colorTextLighter,
  colorBackgroundLighter,
  colorTextDisabled,
  colorTextLight,
  colorTextDefault,
  colorAccentBlue,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {ShortcutHandler} from '../app/ShortcutHandler';
import {buildRepoAddress, DUNDER_REPO_NAME} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {
  NO_RELOAD_PERMISSION_TEXT,
  ReloadRepositoryLocationButton,
} from './ReloadRepositoryLocationButton';
import {RepoSelector, RepoSelectorOption} from './RepoSelector';

interface Props {
  allRepos: RepoSelectorOption[];
  selected: RepoSelectorOption[];
  onToggle: (repoAddresses: RepoAddress[]) => void;
}

export const RepoNavItem = (props: Props) => {
  const {allRepos, selected, onToggle} = props;
  const [open, setOpen] = React.useState(false);

  const summary = () => {
    if (allRepos.length === 0) {
      return <span style={{color: colorTextLighter()}}>No definitions</span>;
    }
    if (allRepos.length === 1) {
      return <SingleRepoSummary repo={allRepos[0]!} onlyRepo />;
    }
    if (selected.length === 1) {
      const selectedRepo = selected[0]!;
      return <SingleRepoSummary repo={selectedRepo} onlyRepo={false} />;
    }
    return <span>{`${selected.length} of ${allRepos.length} shown`}</span>;
  };

  return (
    <Box
      background={colorBackgroundLighter()}
      padding={{vertical: 12, left: 24, right: 20}}
      border="top"
    >
      <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
          <Icon name="folder" />
          <SummaryText>{summary()}</SummaryText>
        </Box>
        {allRepos.length > 1 ? (
          <>
            <Dialog
              canOutsideClickClose
              canEscapeKeyClose
              isOpen={open}
              style={{width: 'auto'}}
              onClose={() => setOpen(false)}
            >
              <DialogHeader icon="repo" label="Definitions" />
              <RepoSelector
                options={allRepos}
                onBrowse={() => setOpen(false)}
                onToggle={onToggle}
                selected={selected}
              />
              <DialogFooter>
                <Box padding={{top: 8}}>
                  <Button intent="none" onClick={() => setOpen(false)}>
                    Done
                  </Button>
                </Box>
              </DialogFooter>
            </Dialog>
            <Box margin={{left: 4}}>
              <Button onClick={() => setOpen(true)}>Filter</Button>
            </Box>
          </>
        ) : null}
      </Box>
    </Box>
  );
};

const SingleRepoSummary = ({repo, onlyRepo}: {repo: RepoSelectorOption; onlyRepo: boolean}) => {
  const repoAddress = buildRepoAddress(repo.repository.name, repo.repositoryLocation.name);
  const isDunder = repoAddress.name === DUNDER_REPO_NAME;
  return (
    <Group direction="row" spacing={4} alignItems="center">
      <SingleRepoNameLink
        to={workspacePathFromAddress(repoAddress)}
        title={repoAddressAsHumanString(repoAddress)}
        $onlyRepo={onlyRepo}
      >
        {isDunder ? repoAddress.location : repoAddress.name}
      </SingleRepoNameLink>
      <ReloadRepositoryLocationButton
        location={repoAddress.location}
        ChildComponent={({codeLocation, tryReload, reloading, hasReloadPermission}) => {
          return (
            <ShortcutHandler
              onShortcut={() => {
                if (hasReloadPermission) {
                  tryReload();
                }
              }}
              shortcutLabel="⌥R"
              shortcutFilter={(e) => e.code === 'KeyR' && e.altKey}
            >
              <ReloadTooltip
                placement="top"
                content={
                  hasReloadPermission ? (
                    <Reloading>
                      {reloading ? (
                        'Reloading…'
                      ) : (
                        <>
                          Reload location <strong>{codeLocation}</strong>
                        </>
                      )}
                    </Reloading>
                  ) : (
                    NO_RELOAD_PERMISSION_TEXT
                  )
                }
              >
                {reloading ? (
                  <Spinner purpose="body-text" />
                ) : (
                  <ReloadButton disabled={!hasReloadPermission} onClick={tryReload}>
                    <Icon
                      name="refresh"
                      color={hasReloadPermission ? colorTextLight() : colorTextDisabled()}
                    />
                  </ReloadButton>
                )}
              </ReloadTooltip>
            </ShortcutHandler>
          );
        }}
      />
    </Group>
  );
};

const SummaryText = styled.div`
  user-select: none;

  /* Line-height preserves container height even when no button is visible. */
  line-height: 32px;
`;

const SingleRepoNameLink = styled(Link)<{$onlyRepo: boolean}>`
  color: ${colorTextLight()};
  display: block;
  max-width: ${({$onlyRepo}) => ($onlyRepo ? '248px' : '192px')};
  overflow-x: hidden;
  text-overflow: ellipsis;
  transition: color 100ms linear;

  &&:hover {
    color: ${colorTextDefault()};
  }

  &&:hover,
  &&:active {
    color: ${colorTextDefault()};
    text-decoration: none;
  }
`;

const ReloadTooltip = styled(Tooltip)`
  && {
    display: block;
  }
`;

const ReloadButton = styled.button`
  background-color: transparent;
  border: none;
  cursor: pointer;
  display: block;
  font-size: 12px;
  padding: 8px;
  margin: -8px;

  :focus:not(:focus-visible) {
    outline: none;
  }

  & ${IconWrapper} {
    transition: color 0.1s ease-in-out;
  }

  :hover ${IconWrapper} {
    color: ${colorAccentBlue()};
  }
`;

const Reloading = styled.div`
  overflow-x: hidden;
  text-overflow: ellipsis;
  max-width: 600px;
  white-space: nowrap;
`;
