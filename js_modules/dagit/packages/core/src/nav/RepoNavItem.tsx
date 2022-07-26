import {
  Box,
  Button,
  Colors,
  DialogFooter,
  DialogHeader,
  Dialog,
  Group,
  Icon,
  IconWrapper,
  Spinner,
  Tooltip,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {usePermissions} from '../app/Permissions';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {ReloadRepositoryLocationButton} from './ReloadRepositoryLocationButton';
import {RepoSelector, RepoSelectorOption} from './RepoSelector';

interface Props {
  allRepos: RepoSelectorOption[];
  selected: RepoSelectorOption[];
  onToggle: (repoAddresses: RepoAddress[]) => void;
}

export const RepoNavItem: React.FC<Props> = (props) => {
  const {allRepos, selected, onToggle} = props;
  const [open, setOpen] = React.useState(false);

  const summary = () => {
    if (allRepos.length === 0) {
      return <span style={{color: Colors.Gray700}}>No repositories</span>;
    }
    if (allRepos.length === 1) {
      return <SingleRepoSummary repo={allRepos[0]} onlyRepo />;
    }
    if (selected.length === 1) {
      const selectedRepo = Array.from(selected)[0];
      return <SingleRepoSummary repo={selectedRepo} onlyRepo={false} />;
    }
    return <span>{`${selected.length} of ${allRepos.length} shown`}</span>;
  };

  return (
    <Box
      background={Colors.Gray50}
      padding={{vertical: 12, left: 24, right: 20}}
      border={{side: 'top', width: 1, color: Colors.KeylineGray}}
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
              <DialogHeader icon="repo" label="Repositories" />
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

const SingleRepoSummary: React.FC<{repo: RepoSelectorOption; onlyRepo: boolean}> = ({
  repo,
  onlyRepo,
}) => {
  const repoAddress = buildRepoAddress(repo.repository.name, repo.repositoryLocation.name);
  const {canReloadRepositoryLocation} = usePermissions();
  return (
    <Group direction="row" spacing={4} alignItems="center">
      <SingleRepoNameLink
        to={workspacePathFromAddress(repoAddress)}
        title={repoAddressAsString(repoAddress)}
        $onlyRepo={onlyRepo}
      >
        {repoAddress.name}
      </SingleRepoNameLink>
      {canReloadRepositoryLocation.enabled ? (
        <ReloadRepositoryLocationButton location={repoAddress.location}>
          {({tryReload, reloading}) => (
            <ShortcutHandler
              onShortcut={tryReload}
              shortcutLabel="⌥R"
              shortcutFilter={(e) => e.code === 'KeyR' && e.altKey}
            >
              <ReloadTooltip
                placement="top"
                content={
                  <Reloading>
                    {reloading ? (
                      'Reloading…'
                    ) : (
                      <>
                        Reload location <strong>{repoAddress.location}</strong>
                      </>
                    )}
                  </Reloading>
                }
              >
                {reloading ? (
                  <Spinner purpose="body-text" />
                ) : (
                  <ReloadButton onClick={tryReload}>
                    <Icon name="refresh" color={Colors.Gray900} />
                  </ReloadButton>
                )}
              </ReloadTooltip>
            </ShortcutHandler>
          )}
        </ReloadRepositoryLocationButton>
      ) : null}
    </Group>
  );
};

const SummaryText = styled.div`
  user-select: none;

  /* Line-height preserves container height even when no button is visible. */
  line-height: 32px;
`;

const SingleRepoNameLink = styled(Link)<{$onlyRepo: boolean}>`
  color: ${Colors.Gray900};
  display: block;
  max-width: ${({$onlyRepo}) => ($onlyRepo ? '248px' : '192px')};
  overflow-x: hidden;
  text-overflow: ellipsis;
  transition: color 100ms linear;

  && {
    color: ${Colors.Gray900};
  }

  &&:hover,
  &&:active {
    color: ${Colors.Gray800};
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
    color: ${Colors.Blue200};
  }
`;

const Reloading = styled.div`
  overflow-x: hidden;
  text-overflow: ellipsis;
  max-width: 600px;
  white-space: nowrap;
`;
