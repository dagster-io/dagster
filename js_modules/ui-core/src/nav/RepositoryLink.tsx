import {
  Box,
  Colors,
  Icon,
  MiddleTruncate,
  Spinner,
  Tooltip,
  UnstyledButton,
} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {
  NO_RELOAD_PERMISSION_TEXT,
  ReloadRepositoryLocationButton,
} from './ReloadRepositoryLocationButton';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';
import styles from './css/RepositoryLink.module.css';

interface Props {
  repoAddress: RepoAddress;
  showIcon?: boolean;
  showRefresh?: boolean;
}

export const RepositoryLink = ({repoAddress, showIcon = false, showRefresh = true}: Props) => {
  const {location} = repoAddress;
  const repoString = repoAddressAsHumanString(repoAddress);

  return (
    <Box flex={{display: 'inline-flex', direction: 'row', alignItems: 'center'}} title={repoString}>
      {showIcon ? (
        <Box margin={{right: 8}}>
          <Icon name="folder" color={Colors.accentGray()} />
        </Box>
      ) : null}
      <Link className={styles.repositoryName} to={workspacePathFromAddress(repoAddress)}>
        <MiddleTruncate text={repoString} />
      </Link>
      {showRefresh ? (
        <Box margin={{left: 4}} className={styles.buttonContainer}>
          <ReloadRepositoryLocationButton
            location={location}
            ChildComponent={({codeLocation, tryReload, reloading, hasReloadPermission}) => {
              const tooltipContent = () => {
                if (!hasReloadPermission) {
                  return NO_RELOAD_PERMISSION_TEXT;
                }

                return reloading ? (
                  'Reloading…'
                ) : (
                  <>
                    Reload location <strong>{codeLocation}</strong>
                  </>
                );
              };

              return (
                <Tooltip content={tooltipContent()} display="block">
                  {reloading ? (
                    <Spinner purpose="body-text" />
                  ) : (
                    <UnstyledButton disabled={!hasReloadPermission} onClick={tryReload}>
                      <Icon
                        name="refresh"
                        color={hasReloadPermission ? Colors.accentGray() : Colors.accentGrayHover()}
                      />
                    </UnstyledButton>
                  )}
                </Tooltip>
              );
            }}
          />
        </Box>
      ) : null}
    </Box>
  );
};
