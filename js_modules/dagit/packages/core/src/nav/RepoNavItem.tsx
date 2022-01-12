import {
  Box,
  ButtonWIP,
  ColorsWIP,
  DialogFooter,
  DialogHeader,
  DialogWIP,
  Group,
  IconWIP,
  IconWrapper,
  Spinner,
  Tooltip,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {usePermissions} from '../app/Permissions';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {ReloadRepositoryLocationButton} from './ReloadRepositoryLocationButton';
import {RepoDetails, RepoSelector} from './RepoSelector';

interface Props {
  allRepos: RepoDetails[];
  selected: Set<RepoDetails>;
  onToggle: (repoAddress: RepoDetails) => void;
}

export const RepoNavItem: React.FC<Props> = (props) => {
  const {allRepos, selected, onToggle} = props;
  const [open, setOpen] = React.useState(false);

  const summary = () => {
    if (allRepos.length === 0) {
      return <span style={{color: ColorsWIP.Gray700}}>No repositories</span>;
    }
    if (allRepos.length === 1) {
      return <SingleRepoSummary repoAddress={allRepos[0].repoAddress} />;
    }
    if (selected.size === 1) {
      const selectedRepo = Array.from(selected)[0];
      return <SingleRepoSummary repoAddress={selectedRepo.repoAddress} />;
    }
    return <span>{`${selected.size} of ${allRepos.length} shown`}</span>;
  };

  return (
    <Box
      background={ColorsWIP.Gray50}
      padding={{vertical: 12, left: 24, right: 20}}
      border={{side: 'top', width: 1, color: ColorsWIP.KeylineGray}}
    >
      <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
          <IconWIP name="folder" />
          <SummaryText>{summary()}</SummaryText>
        </Box>
        {allRepos.length > 1 ? (
          <>
            <DialogWIP
              canOutsideClickClose
              canEscapeKeyClose
              isOpen={open}
              style={{width: 'auto'}}
              onClose={() => setOpen(false)}
            >
              <DialogHeader icon="repo" label="Repositories" />
              <div>
                <Box padding={{vertical: 8, horizontal: 24}}>
                  {`${selected.size} of ${allRepos.length} selected`}
                </Box>
                <RepoSelector
                  options={allRepos}
                  onBrowse={() => setOpen(false)}
                  onToggle={onToggle}
                  selected={selected}
                />
              </div>
              <DialogFooter>
                <Box padding={{top: 8}}>
                  <ButtonWIP intent="none" onClick={() => setOpen(false)}>
                    Done
                  </ButtonWIP>
                </Box>
              </DialogFooter>
            </DialogWIP>
            <ButtonWIP onClick={() => setOpen(true)}>Filter</ButtonWIP>
          </>
        ) : null}
      </Box>
    </Box>
  );
};

const SingleRepoSummary: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  const {canReloadRepositoryLocation} = usePermissions();
  return (
    <Group direction="row" spacing={4} alignItems="center">
      <SingleRepoNameLink
        to={workspacePathFromAddress(repoAddress)}
        title={repoAddressAsString(repoAddress)}
      >
        {repoAddress.name}
      </SingleRepoNameLink>
      {canReloadRepositoryLocation ? (
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
                    <IconWIP name="refresh" color={ColorsWIP.Gray900} />
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

const SingleRepoNameLink = styled(Link)`
  color: ${ColorsWIP.Gray900};
  display: block;
  max-width: 234px;
  overflow-x: hidden;
  text-overflow: ellipsis;
  transition: color 100ms linear;

  && {
    color: ${ColorsWIP.Gray900};
  }

  &&:hover,
  &&:active {
    color: ${ColorsWIP.Gray800};
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
    color: ${ColorsWIP.Blue200};
  }
`;

const Reloading = styled.div`
  overflow-x: hidden;
  text-overflow: ellipsis;
  max-width: 600px;
  white-space: nowrap;
`;
