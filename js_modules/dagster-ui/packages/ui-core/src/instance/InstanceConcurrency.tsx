import {
  Box,
  Button,
  ButtonLink,
  Dialog,
  DialogBody,
  DialogFooter,
  Heading,
  Icon,
  MetadataTableWIP,
  Mono,
  NonIdealState,
  Page,
  PageHeader,
  SpinnerWithText,
  Subheading,
  TextInput,
} from '@dagster-io/ui-components';
import {StyledRawCodeMirror} from '@dagster-io/ui-components/editor';
import * as React from 'react';
import {useParams} from 'react-router-dom';

import {ConcurrencyTab, ConcurrencyTabs} from './ConcurrencyTabs';
import {InstanceConcurrencyKeyInfo, isValidLimit} from './InstanceConcurrencyKeyInfo';
import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {ConcurrencyTable} from './VirtualizedInstanceConcurrencyTable';
import {gql, useMutation, useQuery} from '../apollo-client';
import {
  InstanceConcurrencyLimitsQuery,
  InstanceConcurrencyLimitsQueryVariables,
  RunQueueConfigFragment,
  SetConcurrencyLimitMutation,
  SetConcurrencyLimitMutationVariables,
} from './types/InstanceConcurrency.types';
import {QueryRefreshState} from '../app/QueryRefresh';
import {COMMON_COLLATOR} from '../app/Util';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

const DEFAULT_MIN_VALUE = 1;
const DEFAULT_MAX_VALUE = 1000;

export const InstanceConcurrencyPageContent = React.memo(() => {
  const {concurrencyKey} = useParams<{concurrencyKey?: string}>();
  if (!concurrencyKey) {
    return <InstanceConcurrencyIndexContent />;
  }

  const decodedKey = decodeURIComponent(concurrencyKey);
  return <InstanceConcurrencyKeyInfo concurrencyKey={decodedKey} />;
});

export const InstanceConcurrencyIndexContent = React.memo(() => {
  useTrackPageView();
  useDocumentTitle('Concurrency');
  const queryResult = useQuery<
    InstanceConcurrencyLimitsQuery,
    InstanceConcurrencyLimitsQueryVariables
  >(INSTANCE_CONCURRENCY_LIMITS_QUERY, {
    notifyOnNetworkStatusChange: true,
  });
  const [activeTab, setActiveTab] = React.useState<ConcurrencyTab>('key-concurrency');

  const {data} = queryResult;

  const content = () => {
    if (!data) {
      return (
        <Box padding={{vertical: 64}} flex={{direction: 'column', alignItems: 'center'}}>
          <SpinnerWithText label="Loading concurrency information…" />
        </Box>
      );
    }

    if (activeTab === 'run-concurrency') {
      return (
        <div style={{overflowY: 'auto'}}>
          <RunConcurrencyContent
            hasRunQueue={!!data?.instance.runQueuingSupported}
            runQueueConfig={data?.instance.runQueueConfig}
          />
        </div>
      );
    }

    return (
      <div style={{overflowY: 'hidden'}}>
        <ConcurrencyLimits
          concurrencyKeys={data.instance.concurrencyLimits.map((limit) => limit.concurrencyKey)}
          hasSupport={data.instance.supportsConcurrencyLimits}
          refetch={queryResult.refetch}
          minValue={data.instance.minConcurrencyLimitValue}
          maxValue={data.instance.maxConcurrencyLimitValue}
        />
      </div>
    );
  };

  return (
    <>
      <RunConcurrencyLimitHeader activeTab={activeTab} onChange={setActiveTab} />
      {content()}
    </>
  );
});

export const InstanceConcurrencyPage = () => {
  const {pageTitle} = React.useContext(InstancePageContext);
  return (
    <Page style={{padding: 0}}>
      <PageHeader
        title={<Heading>{pageTitle}</Heading>}
        tabs={<InstanceTabs tab="concurrency" />}
      />
      <InstanceConcurrencyIndexContent />
    </Page>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default InstanceConcurrencyPage;

export const RunConcurrencyContent = ({
  hasRunQueue,
  runQueueConfig,
}: {
  hasRunQueue: boolean;
  runQueueConfig: RunQueueConfigFragment | null | undefined;
  refreshState?: QueryRefreshState;
}) => {
  if (!hasRunQueue) {
    return (
      <>
        <Box
          padding={{vertical: 16, horizontal: 24}}
          border="bottom"
          flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        >
          <Subheading>Run tag concurrency</Subheading>
        </Box>
        <Box padding={{vertical: 16, horizontal: 24}}>
          Run concurrency is not supported with this run coordinator. To enable run concurrency
          limits, configure your instance to use the <Mono>QueuedRunCoordinator</Mono> in your{' '}
          <Mono>dagster.yaml</Mono>. See the{' '}
          <a
            target="_blank"
            rel="noreferrer"
            href="https://docs.dagster.io/deployment/dagster-instance#queuedruncoordinator"
          >
            QueuedRunCoordinator documentation
          </a>{' '}
          for more information.
        </Box>
      </>
    );
  }

  const infoContent = (
    <Box padding={{vertical: 24, horizontal: 24}}>
      Run tag concurrency can be set in your deployment settings. See the{' '}
      <a
        target="_blank"
        rel="noreferrer"
        href="https://docs.dagster.io/guides/limiting-concurrency-in-data-pipelines#configuring-run-level-concurrency"
      >
        concurrency documentation
      </a>{' '}
      for more information.
    </Box>
  );

  const settingsContent = runQueueConfig ? (
    <MetadataTableWIP style={{marginLeft: -1}}>
      <tbody>
        <tr>
          <td>Max concurrent runs:</td>
          <td>{runQueueConfig.maxConcurrentRuns}</td>
        </tr>
        <tr>
          <td>Tag concurrency limits:</td>
          <td>
            {runQueueConfig.tagConcurrencyLimitsYaml ? (
              <StyledRawCodeMirror
                value={runQueueConfig.tagConcurrencyLimitsYaml}
                options={{readOnly: true, lineNumbers: true, mode: 'yaml'}}
              />
            ) : (
              '-'
            )}
          </td>
        </tr>
      </tbody>
    </MetadataTableWIP>
  ) : null;

  return (
    <Box>
      {infoContent}
      {settingsContent}
    </Box>
  );
};

const RunConcurrencyLimitHeader = ({
  activeTab,
  onChange,
}: {
  activeTab: ConcurrencyTab;
  onChange: (tab: ConcurrencyTab) => void;
}) => {
  return (
    <Box
      flex={{justifyContent: 'space-between', alignItems: 'center'}}
      padding={{horizontal: 24}}
      border="bottom"
    >
      <ConcurrencyTabs activeTab={activeTab} onChange={onChange} />
    </Box>
  );
};

export const ConcurrencyLimits = ({
  hasSupport,
  concurrencyKeys,
  refetch,
  minValue,
  maxValue,
}: {
  concurrencyKeys: string[];
  refetch: () => void;
  hasSupport?: boolean;
  maxValue?: number;
  minValue?: number;
  selectedKey?: string | null;
  onSelectKey?: (key: string | undefined) => void;
}) => {
  const [showAdd, setShowAdd] = React.useState<boolean>(false);
  const [search, setSearch] = React.useState('');

  const onAdd = () => setShowAdd(true);

  const sortedKeys = React.useMemo(() => {
    return [...concurrencyKeys]
      .filter((key) => key.includes(search))
      .sort((a, b) => COMMON_COLLATOR.compare(a, b));
  }, [concurrencyKeys, search]);

  if (!hasSupport) {
    return (
      <>
        <ConcurrencyLimitHeader />
        <Box margin={24}>
          <NonIdealState
            icon="error"
            title="No concurrency support"
            description={
              'This instance does not currently support pool-based concurrency limits. You may ' +
              'need to run `dagster instance migrate` to add the necessary tables to your ' +
              'dagster storage to support this feature.'
            }
          />
        </Box>
      </>
    );
  }

  return (
    <Box flex={{direction: 'column'}} style={{overflow: 'auto', height: '100%'}}>
      <ConcurrencyLimitHeader onAdd={onAdd} search={search} setSearch={setSearch} />
      {concurrencyKeys.length === 0 ? (
        <Box margin={24}>
          <NonIdealState
            icon="error"
            title="No pool limits"
            description={
              <>
                No pool limits have been configured for this instance.&nbsp;
                <ButtonLink onClick={() => onAdd()}>Add a pool limit</ButtonLink>.
              </>
            }
          />
        </Box>
      ) : !sortedKeys.length ? (
        <Box padding={16}>
          <NonIdealState
            icon="no-results"
            title="No pool limits"
            description="No pool limits matching the filter."
          />
        </Box>
      ) : (
        <ConcurrencyTable concurrencyKeys={sortedKeys} />
      )}
      <AddConcurrencyLimitDialog
        open={!!showAdd}
        onClose={() => setShowAdd(false)}
        onComplete={refetch}
        minValue={minValue ?? DEFAULT_MIN_VALUE}
        maxValue={maxValue ?? DEFAULT_MAX_VALUE}
      />
    </Box>
  );
};

const ConcurrencyLimitHeader = ({
  onAdd,
  setSearch,
  search,
}: {
  onAdd?: () => void;
} & (
  | {
      setSearch: (searchString: string) => void;
      search: string;
    }
  | {setSearch?: never; search?: never}
)) => {
  return (
    <Box flex={{direction: 'column'}}>
      {setSearch ? (
        <Box
          flex={{direction: 'row', justifyContent: 'space-between'}}
          padding={{vertical: 16, horizontal: 24}}
          border="bottom"
        >
          <TextInput
            value={search || ''}
            style={{width: '30vw', minWidth: 150, maxWidth: 400}}
            placeholder="Filter pools"
            onChange={(e: React.ChangeEvent<any>) => setSearch(e.target.value)}
          />
          {onAdd ? (
            <Button icon={<Icon name="add_circle" />} onClick={() => onAdd()}>
              Add pool limit
            </Button>
          ) : null}
        </Box>
      ) : null}
    </Box>
  );
};

const AddConcurrencyLimitDialog = ({
  open,
  onClose,
  onComplete,
  maxValue,
  minValue,
}: {
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
  maxValue: number;
  minValue: number;
}) => {
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [limitInput, setLimitInput] = React.useState('');
  const [keyInput, setKeyInput] = React.useState('');

  React.useEffect(() => {
    setLimitInput('');
    setKeyInput('');
  }, [open]);

  const [setConcurrencyLimit] = useMutation<
    SetConcurrencyLimitMutation,
    SetConcurrencyLimitMutationVariables
  >(SET_CONCURRENCY_LIMIT_MUTATION);
  const save = async () => {
    setIsSubmitting(true);
    await setConcurrencyLimit({
      variables: {concurrencyKey: keyInput, limit: parseInt(limitInput.trim())},
    });
    setIsSubmitting(false);
    onComplete();
    onClose();
  };

  return (
    <Dialog isOpen={open} title="Add pool limit" onClose={onClose}>
      <DialogBody>
        <Box margin={{bottom: 4}}>Pool:</Box>
        <Box margin={{bottom: 16}}>
          <TextInput
            value={keyInput || ''}
            onChange={(e) => setKeyInput(e.target.value)}
            placeholder="Pool"
          />
        </Box>
        <Box margin={{bottom: 4}}>
          Pool limit ({minValue}-{maxValue}):
        </Box>
        <Box>
          <TextInput
            value={limitInput || ''}
            onChange={(e) => setLimitInput(e.target.value)}
            placeholder={`${minValue} - ${maxValue}`}
          />
        </Box>
      </DialogBody>
      <DialogFooter>
        <Button intent="none" onClick={onClose}>
          Cancel
        </Button>
        <Button
          intent="primary"
          onClick={save}
          disabled={
            !isValidLimit(limitInput.trim(), minValue, maxValue) || !keyInput || isSubmitting
          }
        >
          {isSubmitting ? 'Adding...' : 'Add limit'}
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const RUN_QUEUE_CONFIG_FRAGMENT = gql`
  fragment RunQueueConfigFragment on RunQueueConfig {
    maxConcurrentRuns
    tagConcurrencyLimitsYaml
  }
`;

export const INSTANCE_CONCURRENCY_LIMITS_QUERY = gql`
  query InstanceConcurrencyLimitsQuery {
    instance {
      id
      supportsConcurrencyLimits
      runQueuingSupported
      runQueueConfig {
        ...RunQueueConfigFragment
      }
      minConcurrencyLimitValue
      maxConcurrencyLimitValue
      concurrencyLimits {
        concurrencyKey
      }
    }
  }

  ${RUN_QUEUE_CONFIG_FRAGMENT}
`;

const SET_CONCURRENCY_LIMIT_MUTATION = gql`
  mutation SetConcurrencyLimit($concurrencyKey: String!, $limit: Int!) {
    setConcurrencyLimit(concurrencyKey: $concurrencyKey, limit: $limit)
  }
`;
