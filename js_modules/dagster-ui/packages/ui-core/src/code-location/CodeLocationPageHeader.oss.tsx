import {JoinedButtons, PageHeader} from '@dagster-io/ui-components';
import {useContext} from 'react';

import {CodeLocationPageHeaderTitle} from './CodeLocationPageHeaderTitle';
import {CodeLocationMenu} from '../workspace/CodeLocationMenu';
import {ReloadButton} from '../workspace/CodeLocationRowSet';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
}

export const CodeLocationPageHeader = ({repoAddress}: Props) => {
  const {locationEntries, loading} = useContext(WorkspaceContext);
  const locationEntry = locationEntries.find((entry) => entry.name === repoAddress.location);
  return (
    <PageHeader
      title={<CodeLocationPageHeaderTitle repoAddress={repoAddress} />}
      right={
        loading || !locationEntry ? null : (
          <JoinedButtons>
            <ReloadButton location={repoAddress.location} />
            <CodeLocationMenu locationNode={locationEntry} />
          </JoinedButtons>
        )
      }
    />
  );
};
