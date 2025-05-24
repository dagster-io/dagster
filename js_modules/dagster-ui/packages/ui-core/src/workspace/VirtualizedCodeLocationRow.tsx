import {Box, Colors, JoinedButtons, MiddleTruncate} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import clsx from 'clsx';

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
import {featureEnabled} from '../app/Flags';
import {AnchorButton} from '../ui/AnchorButton';
import {TimeFromNow} from '../ui/TimeFromNow';
import {HeaderCell, HeaderRow, RowCell} from '../ui/VirtualizedTable';
import styles from './VirtualizedCodeLocationRow.module.css';

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

const TEMPLATE_COLUMNS = featureEnabled(FeatureFlag.flagDocsInApp)
  ? '3fr 1fr 1fr 160px 160px'
  : '3fr 1fr 1fr 160px';

interface LocationRowProps {
  locationEntry: WorkspaceRepositoryLocationNode | null;
  locationStatus: LocationStatusEntryFragment;
  hasDocs: boolean;
  index: number;
}

export const VirtualizedCodeLocationRow = React.forwardRef(
  (props: LocationRowProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {locationEntry, locationStatus, hasDocs, index} = props;
    const {name} = locationStatus;
    const repoAddress = buildRepoAddress(DUNDER_REPO_NAME, name);

    return (
      <div ref={ref} data-index={index}>
        <Box
          className={styles.rowGrid}
          style={{'--template-columns': TEMPLATE_COLUMNS}}
          border="bottom"
        >
          <RowCell>
            <Box flex={{direction: 'column', gap: 4}}>
              <div style={{fontWeight: 500}}>
                <Link to={workspacePathFromAddress(repoAddress)}>
                  <MiddleTruncate text={name} />
                </Link>
              </div>
            </Box>
          </RowCell>
          <RowCell>
            <div>
              <LocationStatus locationStatus={locationStatus} locationOrError={locationEntry} />
            </div>
          </RowCell>
          <RowCell>
            <div style={{whiteSpace: 'nowrap'}}>
              <TimeFromNow unixTimestamp={locationStatus.updateTimestamp} />
            </div>
          </RowCell>
          {featureEnabled(FeatureFlag.flagDocsInApp) ? (
            <RowCell>
              {hasDocs ? (
                <div>
                  <AnchorButton to={workspacePathFromAddress(repoAddress, '/docs')}>
                    View docs
                  </AnchorButton>
                </div>
              ) : (
                <span style={{color: Colors.textLighter()}}>None</span>
              )}
            </RowCell>
          ) : null}
          <RowCell>
            <JoinedButtons>
              <ReloadButton location={name} />
              {locationEntry ? <CodeLocationMenu locationNode={locationEntry} /> : null}
            </JoinedButtons>
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
  hasDocs: boolean;
  index: number;
  // measure: (node: Element | null) => void;
}

export const VirtualizedCodeLocationRepositoryRow = React.forwardRef(
  (props: RepoRowProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {locationEntry, locationStatus, repository, hasDocs, index} = props;
    const repoAddress = buildRepoAddress(repository.name, repository.location.name);

    const allMetadata = [...locationEntry.displayMetadata, ...repository.displayMetadata];

    return (
      <div ref={ref} data-index={index}>
        <Box
          className={styles.rowGrid}
          style={{'--template-columns': TEMPLATE_COLUMNS}}
          border="bottom"
        >
          <RowCell>
            <Box flex={{direction: 'column', gap: 4}}>
              <div style={{fontWeight: 500}}>
                <Link to={workspacePathFromAddress(repoAddress)}>
                  <MiddleTruncate text={repoAddressAsHumanString(repoAddress)} />
                </Link>
              </div>
              <ImageName metadata={allMetadata} />
              <ModuleOrPackageOrFile metadata={allMetadata} />
              <RepositoryCountTags repo={repository} repoAddress={repoAddress} />
            </Box>
          </RowCell>
          <RowCell>
            <div>
              <LocationStatus locationStatus={locationStatus} locationOrError={locationEntry} />
            </div>
          </RowCell>
          <RowCell>
            <div style={{whiteSpace: 'nowrap'}}>
              <TimeFromNow unixTimestamp={locationStatus.updateTimestamp} />
            </div>
          </RowCell>
          {featureEnabled(FeatureFlag.flagDocsInApp) ? (
            <RowCell>
              {hasDocs ? (
                <div>
                  <AnchorButton to={workspacePathFromAddress(repoAddress, '/docs')}>
                    View docs
                  </AnchorButton>
                </div>
              ) : (
                <span style={{color: Colors.textLighter()}}>None</span>
              )}
            </RowCell>
          ) : null}
          <RowCell style={{alignItems: 'flex-end'}}>
            <JoinedButtons>
              <ReloadButton location={locationStatus.name} />
              <CodeLocationMenu locationNode={locationEntry} />
            </JoinedButtons>
          </RowCell>
        </Box>
      </div>
    );
  },
);

export const VirtualizedCodeLocationHeader = () => {
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>Name</HeaderCell>
      <HeaderCell>Status</HeaderCell>
      <HeaderCell>Updated</HeaderCell>
      {featureEnabled(FeatureFlag.flagDocsInApp) ? <HeaderCell>Docs</HeaderCell> : null}
      <HeaderCell style={{textAlign: 'right'}}>Actions</HeaderCell>
    </HeaderRow>
  );
};
