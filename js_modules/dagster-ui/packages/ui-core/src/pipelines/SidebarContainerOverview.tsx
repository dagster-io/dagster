import {Box, MetadataTable} from '@dagster-io/ui-components';

import {Description} from './Description';
import {SidebarSection, SidebarSubhead, SidebarTitle} from './SidebarComponents';
import {
  SIDEBAR_RESOURCES_SECTION_FRAGMENT,
  SidebarResourcesSection,
} from './SidebarResourcesSection';
import {SidebarRootContainerFragment} from './types/SidebarContainerOverview.types';
import {gql} from '../apollo-client';
import {breakOnUnderscores} from '../app/Util';
import {MetadataEntry} from '../metadata/MetadataEntry';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntryFragment';
import {findRepositoryAmongOptions, useRepositoryOptions} from '../workspace/WorkspaceContext/util';
import {repoContainsPipeline} from '../workspace/findRepoContainingPipeline';
import {RepoAddress} from '../workspace/types';

export const SidebarContainerOverview = ({
  container,
  repoAddress,
}: {
  container: SidebarRootContainerFragment;
  repoAddress?: RepoAddress;
}) => {
  const {options} = useRepositoryOptions();

  // Determine if the pipeline or job snapshot is tied to a legacy pipeline. This is annoying
  // because snapshots only have a pipeline name + snapshotId, not a repository, but if a repo
  // is passed in we want to use that one.
  let isLegacy = false;
  let isPastSnapshot = false;

  if (container.__typename === 'PipelineSnapshot') {
    const {pipelineSnapshotId, parentSnapshotId} = container;

    const repo = repoAddress
      ? findRepositoryAmongOptions(options, repoAddress)
      : options.find((repo) => repoContainsPipeline(repo, container.name));
    const match = repo && repoContainsPipeline(repo, container.name);

    isLegacy = match ? !match.isJob : false;
    isPastSnapshot =
      match?.pipelineSnapshotId !== pipelineSnapshotId &&
      match?.pipelineSnapshotId !== parentSnapshotId;
  }

  return (
    <div>
      <Box padding={{vertical: 16, horizontal: 24}}>
        <SidebarSubhead>
          {container.__typename === 'Graph' ? 'Graph' : isLegacy ? 'Pipeline' : 'Job'}
          {isPastSnapshot ? ' Snapshot' : ''}
        </SidebarSubhead>
        <SidebarTitle>{breakOnUnderscores(container.name)}</SidebarTitle>
      </Box>

      <SidebarSection title="Description">
        <Box padding={{vertical: 16, horizontal: 24}}>
          <Description description={container.description || 'No description provided'} />
        </Box>
      </SidebarSection>

      {container.__typename === 'PipelineSnapshot' && (
        <SidebarSection title={isLegacy ? 'Modes' : 'Resources'} collapsedByDefault={true}>
          <Box padding={{vertical: 16, horizontal: 24}}>
            {container.modes.map((mode) => (
              <SidebarResourcesSection key={mode.name} mode={mode} showModeName={isLegacy} />
            ))}
          </Box>
        </SidebarSection>
      )}

      {container.__typename === 'PipelineSnapshot' && (
        <SidebarSection title="Metadata">
          <Box padding={{vertical: 16, horizontal: 24}}>
            <MetadataTable
              rows={container.metadataEntries.map((entry) => ({
                key: entry.label,
                value: <MetadataEntry entry={entry} repoLocation={repoAddress?.location} />,
              }))}
            />
          </Box>
        </SidebarSection>
      )}
    </div>
  );
};

export const SIDEBAR_ROOT_CONTAINER_FRAGMENT = gql`
  fragment SidebarRootContainerFragment on SolidContainer {
    id
    name
    description
    modes {
      id
      ...SidebarResourcesSectionFragment
    }
    ... on PipelineSnapshot {
      pipelineSnapshotId
      parentSnapshotId
      metadataEntries {
        ...MetadataEntryFragment
      }
    }
  }

  ${SIDEBAR_RESOURCES_SECTION_FRAGMENT}
  ${METADATA_ENTRY_FRAGMENT}
`;
