import {
  Box,
  Colors,
  FontFamily,
  Icon,
  Mono,
  SpinnerWithText,
  Table,
  Tooltip,
  UnstyledButton,
} from '@dagster-io/ui-components';
import {StyledRawCodeMirror} from '@dagster-io/ui-components/editor';
import {useCallback, useContext, useMemo, useState} from 'react';
import {CodeLocationAlertsSection} from 'shared/code-location/CodeLocationAlertsSection.oss';
import {CodeLocationPageHeader} from 'shared/code-location/CodeLocationPageHeader.oss';
import {CodeLocationServerSection} from 'shared/code-location/CodeLocationServerSection.oss';
import {CodeLocationTabs} from 'shared/code-location/CodeLocationTabs.oss';
import {createGlobalStyle} from 'styled-components';
import * as yaml from 'yaml';

import {CodeLocationOverviewSectionHeader} from './CodeLocationOverviewSectionHeader';
import {useCopyToClipboard} from '../app/browser';
import {TimeFromNow} from '../ui/TimeFromNow';
import {CodeLocationNotFound} from '../workspace/CodeLocationNotFound';
import {LocationStatus} from '../workspace/CodeLocationRowSet';
import {
  WorkspaceContext,
  WorkspaceRepositoryLocationNode,
} from '../workspace/WorkspaceContext/WorkspaceContext';
import {LocationStatusEntryFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import styles from './css/CodeLocationOverviewRoot.module.css';

const RIGHT_COLUMN_WIDTH = '280px';

type MetadataRowKey = 'image';

interface Props {
  repoAddress: RepoAddress;
  locationEntry: WorkspaceRepositoryLocationNode | null;
  locationStatus: LocationStatusEntryFragment | null;
}

export const CodeLocationOverviewRoot = (props: Props) => {
  const {repoAddress, locationStatus, locationEntry} = props;

  const {displayMetadata} = locationEntry || {};
  const metadataForDetails: Record<MetadataRowKey, {key: string; value: string} | null> =
    useMemo(() => {
      return {
        image: displayMetadata?.find(({key}) => key === 'image') || null,
      };
    }, [displayMetadata]);

  const metadataAsYaml = useMemo(() => {
    return yaml.stringify(
      Object.fromEntries((displayMetadata || []).map(({key, value}) => [key, value])),
    );
  }, [displayMetadata]);

  const libraryVersions = useMemo(() => {
    return locationEntry?.locationOrLoadError?.__typename === 'RepositoryLocation'
      ? locationEntry?.locationOrLoadError.dagsterLibraryVersions
      : null;
  }, [locationEntry]);

  const copy = useCopyToClipboard();
  const [didCopy, setDidCopy] = useState(false);

  const onClickCopy = useCallback(() => {
    let timer: NodeJS.Timeout | null = null;
    if (metadataForDetails.image) {
      copy(metadataForDetails.image.value);
      setDidCopy(true);
      timer = setTimeout(() => {
        setDidCopy(false);
      }, 3000);
    }

    return () => {
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [copy, metadataForDetails.image]);

  return (
    <>
      <Box padding={{horizontal: 24}} border="bottom">
        <CodeLocationTabs
          selectedTab="overview"
          repoAddress={repoAddress}
          locationEntry={locationEntry}
        />
      </Box>
      <CodeLocationOverviewSectionHeader label="Details" />
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
              {locationStatus ? (
                <div style={{whiteSpace: 'nowrap'}}>
                  <TimeFromNow unixTimestamp={locationStatus.updateTimestamp} />
                </div>
              ) : null}
            </td>
          </tr>
          {metadataForDetails.image ? (
            <tr>
              <td>Image</td>
              <td style={{fontFamily: FontFamily.monospace}}>
                <div className={styles.imageName}>
                  <span style={{marginRight: '4px'}}>{metadataForDetails.image.value}</span>
                  <Tooltip
                    content={didCopy ? 'Copied!' : 'Click to copy image string'}
                    placement="top"
                  >
                    <UnstyledButton onClick={onClickCopy}>
                      <Icon name={didCopy ? 'done' : 'copy'} size={16} />
                    </UnstyledButton>
                  </Tooltip>
                </div>
              </td>
            </tr>
          ) : null}
        </tbody>
      </Table>
      <CodeLocationServerSection locationName={repoAddress.location} />
      {libraryVersions?.length ? (
        <>
          <CodeLocationOverviewSectionHeader label="Libraries" />
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
      <CodeLocationAlertsSection locationName={repoAddress.location} />
      <CodeLocationOverviewSectionHeader label="Metadata" border="bottom" />
      <CodeLocationMetadataStyle />
      <div style={{height: '320px'}}>
        <StyledRawCodeMirror
          options={{readOnly: true, lineNumbers: false}}
          theme={['code-location-metadata']}
          value={metadataAsYaml}
        />
      </div>
    </>
  );
};

const QueryfulCodeLocationOverviewRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  const {
    locationEntries,
    locationStatuses,
    loadingNonAssets: loading,
  } = useContext(WorkspaceContext);
  const locationEntry = locationEntries.find((entry) => entry.name === repoAddress.location);
  const locationStatus = locationStatuses[repoAddress.location];

  const content = () => {
    if (!locationEntry || !locationStatus) {
      const displayName = repoAddressAsHumanString(repoAddress);
      if (loading) {
        return (
          <Box padding={64} flex={{direction: 'row', justifyContent: 'center'}}>
            <SpinnerWithText label={`Loading ${displayName}…`} />
          </Box>
        );
      }

      if (!locationEntry && !locationStatus) {
        return (
          <Box padding={64} flex={{direction: 'row', justifyContent: 'center'}}>
            <CodeLocationNotFound repoAddress={repoAddress} locationEntry={locationEntry || null} />
          </Box>
        );
      }
    }

    return (
      <CodeLocationOverviewRoot
        repoAddress={repoAddress}
        locationEntry={locationEntry || null}
        locationStatus={locationStatus || null}
      />
    );
  };

  return (
    <>
      <CodeLocationPageHeader repoAddress={repoAddress} />
      {content()}
    </>
  );
};

// eslint-disable-next-line import/no-default-export
export default QueryfulCodeLocationOverviewRoot;

const CodeLocationMetadataStyle = createGlobalStyle`
  .CodeMirror.cm-s-code-location-metadata.cm-s-code-location-metadata {
    background-color: ${Colors.backgroundDefault()};
    padding: 12px 20px;
    height: 300px;
  }
`;
