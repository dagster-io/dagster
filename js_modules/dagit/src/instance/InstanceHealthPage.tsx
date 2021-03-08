import {QueryResult} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';

import {DaemonList} from 'src/instance/DaemonList';
import {InstanceHealthQuery} from 'src/instance/types/InstanceHealthQuery';
import {Group} from 'src/ui/Group';
import {Subheading} from 'src/ui/Text';
import {ReloadAllButton} from 'src/workspace/ReloadAllButton';
import {RepositoryLocationsList} from 'src/workspace/RepositoryLocationsList';

interface Props {
  queryData: QueryResult<InstanceHealthQuery>;
}

export const InstanceHealthPage = (props: Props) => {
  const {queryData} = props;
  const {data, loading} = queryData;

  const daemonContent = () => {
    if (loading && !data?.instance) {
      return <div style={{color: Colors.GRAY3}}>Loading…</div>;
    }
    return data?.instance ? <DaemonList daemonHealth={data.instance.daemonHealth} /> : null;
  };

  return (
    <Group direction="column" spacing={32}>
      <Group direction="column" spacing={16}>
        <Group direction="row" spacing={12} alignItems="center">
          <Subheading id="repository-locations">Workspace</Subheading>
          <ReloadAllButton />
        </Group>
        <RepositoryLocationsList />
      </Group>
      <Group direction="column" spacing={16}>
        <Subheading>Daemon statuses</Subheading>
        {daemonContent()}
      </Group>
    </Group>
  );
};
