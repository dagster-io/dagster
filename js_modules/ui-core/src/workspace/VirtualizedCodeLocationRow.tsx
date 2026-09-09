import {
  Box,
  HeaderCell,
  HeaderRow,
  JoinedButtons,
  MiddleTruncate,
  RowCell,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {CodeLocationMenu} from './CodeLocationMenu';
import {ImageName, LocationStatus, ModuleOrPackageOrFile, ReloadButton} from './CodeLocationRowSet';
import {CodeLocationRowStatusType} from './CodeLocationRowStatusType';
import {RepositoryCountTags} from './RepositoryCountTags';
import {WorkspaceRepositoryLocationNode} from './WorkspaceContext/WorkspaceContext';
import {
  LocationStatusEntryFragment,
  WorkspaceLocationNodeFragment,
  WorkspaceRepositoryFragment,
} from './WorkspaceContext/types/WorkspaceQueries.types';
import {DUNDER_REPO_NAME, buildRepoAddress} from './buildRepoAddress';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {workspacePathFromAddress} from './workspacePath';
import {LayoutContext} from '../app/LayoutProvider';
import {TimeFromNow} from '../ui/TimeFromNow';
import styles from './css/VirtualizedCodeLocationRow.module.css';

export type CodeLocationRowType =
  | {
      type: 'repository';
      locationStatus: LocationStatusEntryFragment;
      locationEntry: WorkspaceLocationNodeFragment;
      repository: WorkspaceRepositoryFragment;
      status: CodeLocationRowStatusType;
    }
  | {
      type: 'location';
      locationStatus: LocationStatusEntryFragment;
      locationEntry: WorkspaceLocationNodeFragment | null;
      status: CodeLocationRowStatusType;
    };

const TEMPLATE_COLUMNS = '3fr 1fr 1fr 160px';

interface LocationRowProps {
  locationEntry: WorkspaceRepositoryLocationNode | null;
  locationStatus: LocationStatusEntryFragment;
  index: number;
}

export const VirtualizedCodeLocationRow = React.forwardRef(
  (props: LocationRowProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {locationEntry, locationStatus, index} = props;
    const {name} = locationStatus;
    const repoAddress = buildRepoAddress(DUNDER_REPO_NAME, name);
    const {isMobileScreen} = React.useContext(LayoutContext).nav;

    return (
      <div ref={ref} data-index={index}>
        <Box border="bottom" className={styles.rowGrid}>
          <RowCell className={styles.cellName}>
            <Box flex={{direction: 'column', gap: 4}}>
              <div style={{fontWeight: 500}}>
                <Link to={workspacePathFromAddress(repoAddress)}>
                  <MiddleTruncate text={name} />
                </Link>
              </div>
            </Box>
          </RowCell>
          <RowCell className={styles.cellStatus}>
            <div>
              <LocationStatus locationStatus={locationStatus} locationOrError={locationEntry} />
            </div>
          </RowCell>
          <RowCell className={styles.cellUpdated}>
            <div style={{whiteSpace: 'nowrap'}}>
              <TimeFromNow unixTimestamp={locationStatus.updateTimestamp} />
            </div>
          </RowCell>
          <RowCell className={styles.cellActions}>
            {isMobileScreen ? (
              locationEntry ? (
                <CodeLocationMenu locationNode={locationEntry} reloadLocation={name} />
              ) : (
                <ReloadButton location={name} />
              )
            ) : (
              <JoinedButtons>
                <ReloadButton location={name} />
                {locationEntry ? <CodeLocationMenu locationNode={locationEntry} /> : null}
              </JoinedButtons>
            )}
          </RowCell>
        </Box>
      </div>
    );
  },
);

interface RepoRowProps {
  locationEntry: WorkspaceRepositoryLocationNode;
  locationStatus: LocationStatusEntryFragment;
  repository: WorkspaceRepositoryFragment;
  index: number;
}

export const VirtualizedCodeLocationRepositoryRow = React.forwardRef(
  (props: RepoRowProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {locationEntry, locationStatus, repository, index} = props;
    const repoAddress = buildRepoAddress(repository.name, repository.location.name);
    const {isMobileScreen} = React.useContext(LayoutContext).nav;

    const allMetadata = [...locationEntry.displayMetadata, ...repository.displayMetadata];

    return (
      <div ref={ref} data-index={index}>
        <Box border="bottom" className={styles.rowGrid}>
          <RowCell className={styles.cellName}>
            <Box flex={{direction: 'column', gap: 4}}>
              <div style={{fontWeight: 500}}>
                <Link to={workspacePathFromAddress(repoAddress)}>
                  <MiddleTruncate text={repoAddressAsHumanString(repoAddress)} />
                </Link>
              </div>
              {isMobileScreen ? null : (
                <>
                  <ImageName metadata={allMetadata} />
                  <ModuleOrPackageOrFile metadata={allMetadata} />
                </>
              )}
              <RepositoryCountTags
                repo={repository}
                repoAddress={repoAddress}
                compact={isMobileScreen}
              />
            </Box>
          </RowCell>
          <RowCell className={styles.cellStatus}>
            <div>
              <LocationStatus locationStatus={locationStatus} locationOrError={locationEntry} />
            </div>
          </RowCell>
          <RowCell className={styles.cellUpdated}>
            <div style={{whiteSpace: 'nowrap'}}>
              <TimeFromNow unixTimestamp={locationStatus.updateTimestamp} />
            </div>
          </RowCell>
          <RowCell className={styles.cellActions} style={{alignItems: 'flex-end'}}>
            {isMobileScreen ? (
              <CodeLocationMenu locationNode={locationEntry} reloadLocation={locationStatus.name} />
            ) : (
              <JoinedButtons>
                <ReloadButton location={locationStatus.name} />
                <CodeLocationMenu locationNode={locationEntry} />
              </JoinedButtons>
            )}
          </RowCell>
        </Box>
      </div>
    );
  },
);

export const VirtualizedCodeLocationHeader = () => {
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky className={styles.tableHeader}>
      <HeaderCell>Name</HeaderCell>
      <HeaderCell>Status</HeaderCell>
      <HeaderCell>Updated</HeaderCell>
      <HeaderCell style={{textAlign: 'right'}}>Actions</HeaderCell>
    </HeaderRow>
  );
};
