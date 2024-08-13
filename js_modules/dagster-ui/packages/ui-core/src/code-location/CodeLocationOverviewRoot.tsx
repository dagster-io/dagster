import {
  Box,
  Colors,
  FontFamily,
  Heading,
  MiddleTruncate,
  Mono,
  PageHeader,
  StyledRawCodeMirror,
  Subheading,
  Table,
} from '@dagster-io/ui-components';
import {ComponentProps, ReactNode, useMemo} from 'react';
import {Link} from 'react-router-dom';
import {createGlobalStyle} from 'styled-components';
import * as yaml from 'yaml';

import {CodeLocationTabs} from './CodeLocationTabs';
import {TimeFromNow} from '../ui/TimeFromNow';
import {LocationStatus} from '../workspace/CodeLocationRowSet';
import {WorkspaceRepositoryLocationNode} from '../workspace/WorkspaceContext';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {LocationStatusEntryFragment} from '../workspace/types/WorkspaceQueries.types';

const RIGHT_COLUMN_WIDTH = '280px';

type MetadataRowKey = 'image';

interface Props {
  repoAddress: RepoAddress;
  locationEntry: WorkspaceRepositoryLocationNode;
  locationStatus: LocationStatusEntryFragment;
}

export const CodeLocationOverviewRoot = (props: Props) => {
  const {repoAddress, locationStatus, locationEntry} = props;

  const {displayMetadata} = locationEntry;
  const metadataForDetails: Record<MetadataRowKey, {key: string; value: string} | null> =
    useMemo(() => {
      return {
        image: displayMetadata.find(({key}) => key === 'image') || null,
      };
    }, [displayMetadata]);

  const metadataAsYaml = useMemo(() => {
    return yaml.stringify(Object.fromEntries(displayMetadata.map(({key, value}) => [key, value])));
  }, [displayMetadata]);

  const libraryVersions = useMemo(() => {
    return locationEntry.locationOrLoadError?.__typename === 'RepositoryLocation'
      ? locationEntry.locationOrLoadError.dagsterLibraryVersions
      : null;
  }, [locationEntry]);

  return (
    <>
      <PageHeader
        title={
          <Heading>
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <div>
                <Link to="/locations">Code locations</Link>
              </div>
              <div>/</div>
              <div>{repoAddressAsHumanString(repoAddress)}</div>
            </Box>
          </Heading>
        }
      />
      <Box padding={{horizontal: 24}} border="bottom">
        <CodeLocationTabs selectedTab="overview" repoAddress={repoAddress} />
      </Box>
      <SectionHeader label="Details" />
      {/* Fixed table layout to contain overflowing strings in right column */}
      <Table style={{width: '100%', tableLayout: 'fixed'}}>
        <tbody>
          <tr>
            <td
              style={{
                width: RIGHT_COLUMN_WIDTH,
                minWidth: RIGHT_COLUMN_WIDTH,
                verticalAlign: 'middle',
              }}
            >
              Status
            </td>
            <td>
              <LocationStatus locationStatus={locationStatus} locationOrError={locationEntry} />
            </td>
          </tr>
          <tr>
            <td>Updated</td>
            <td>
              <div style={{whiteSpace: 'nowrap'}}>
                <TimeFromNow unixTimestamp={locationStatus.updateTimestamp} />
              </div>
            </td>
          </tr>
          {metadataForDetails.image ? (
            <tr>
              <td>Image</td>
              <td style={{fontFamily: FontFamily.monospace}}>
                <MiddleTruncate text={metadataForDetails.image.value} />
              </td>
            </tr>
          ) : null}
        </tbody>
      </Table>
      {libraryVersions?.length ? (
        <>
          <SectionHeader label="Libraries" />
          <Table>
            <tbody>
              {libraryVersions.map((version) => (
                <tr key={version.name}>
                  <td style={{width: RIGHT_COLUMN_WIDTH}}>
                    <Mono>{version.name}</Mono>
                  </td>
                  <td>
                    <Mono>{version.version}</Mono>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </>
      ) : null}
      <SectionHeader label="Metadata" border="bottom" />
      <CodeLocationMetadataStyle />
      <StyledRawCodeMirror
        options={{readOnly: true, lineNumbers: false}}
        theme={['code-location-metadata']}
        value={metadataAsYaml}
      />
    </>
  );
};

const CodeLocationMetadataStyle = createGlobalStyle`
  .CodeMirror.cm-s-code-location-metadata.cm-s-code-location-metadata {
    background-color: ${Colors.backgroundDefault()};
    padding: 12px 20px;
  }
`;

const SectionHeader = ({
  label,
  border = null,
}: {
  label: ReactNode;
  border?: ComponentProps<typeof Box>['border'];
}) => (
  <Box
    background={Colors.backgroundLight()}
    border={border}
    padding={{horizontal: 24, vertical: 8}}
  >
    <Subheading>{label}</Subheading>
  </Box>
);
