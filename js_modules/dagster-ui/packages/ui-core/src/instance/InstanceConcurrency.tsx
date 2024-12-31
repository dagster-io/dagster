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
  Spinner,
  Subheading,
  Tag,
  TextInput,
} from '@dagster-io/ui-components';
import {StyledRawCodeMirror} from '@dagster-io/ui-components/editor';
import * as React from 'react';
import {useParams} from 'react-router-dom';

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
import {useFeatureFlags} from '../app/Flags';
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

  return <InstanceConcurrencyKeyInfo concurrencyKey={concurrencyKey} />;
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
  const {flagPoolUI} = useFeatureFlags();

  const {data} = queryResult;
  const poolsContent = data ? (
    <ConcurrencyLimits
      concurrencyKeys={data.instance.concurrencyLimits.map((limit) => limit.concurrencyKey)}
      hasSupport={data.instance.supportsConcurrencyLimits}
      refetch={queryResult.refetch}
      minValue={data.instance.minConcurrencyLimitValue}
      maxValue={data.instance.maxConcurrencyLimitValue}
    />
  ) : null;
  const runTagsContent = (
    <RunConcurrencyContent
      hasRunQueue={!!data?.instance.runQueuingSupported}
      runQueueConfig={data?.instance.runQueueConfig}
    />
  );

  return (
    <div style={{overflowY: 'auto'}}>
      {data ? (
        <>
          <Box flex={{direction: 'column', gap: 64}}>
            {flagPoolUI ? (
              <>
                {poolsContent}
                {runTagsContent}
              </>
            ) : (
              <>
                {runTagsContent}
                {poolsContent}
              </>
            )}
          </Box>
        </>
      ) : (
        <Box padding={{vertical: 64}}>
          <Spinner purpose="section" />
        </Box>
      )}
    </div>
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
  onEdit,
}: {
  hasRunQueue: boolean;
  runQueueConfig: RunQueueConfigFragment | null | undefined;
  refreshState?: QueryRefreshState;
  onEdit?: () => void;
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

  const settings_content = runQueueConfig ? (
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
      <RunConcurrencyLimitHeader onEdit={onEdit} />
      {infoContent}
      {settings_content}
    </Box>
  );
};

const RunConcurrencyLimitHeader = ({onEdit}: {onEdit?: () => void}) => (
  <Box
    flex={{justifyContent: 'space-between', alignItems: 'center'}}
    padding={{vertical: 16, horizontal: 24}}
    border="bottom"
  >
    <Subheading>Run concurrency</Subheading>
    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
      {onEdit ? (
        <Button icon={<Icon name="edit" />} onClick={() => onEdit()}>
          Edit configuration
        </Button>
      ) : null}
    </Box>
  </Box>
);

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

  const {flagPoolUI} = useFeatureFlags();

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
            title={flagPoolUI ? 'No pool limits' : 'No concurrency limits'}
            description={
              flagPoolUI ? (
                <>
                  No pool limits have been configured for this instance.&nbsp;
                  <ButtonLink onClick={() => onAdd()}>Add a pool limit</ButtonLink>.
                </>
              ) : (
                <>
                  No concurrency limits have been configured for this instance.&nbsp;
                  <ButtonLink onClick={() => onAdd()}>Add a concurrency limit</ButtonLink>.
                </>
              )
            }
          />
        </Box>
      ) : !sortedKeys.length ? (
        <Box padding={16}>
          <NonIdealState
            icon="no-results"
            title={flagPoolUI ? 'No pool limits' : 'No concurrency limits'}
            description={
              flagPoolUI
                ? 'No pool limits matching the filter.'
                : 'No concurrency limits matching the filter.'
            }
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
  const {flagPoolUI} = useFeatureFlags();
  return (
    <Box flex={{direction: 'column'}}>
      <Box
        flex={{justifyContent: 'space-between', alignItems: 'center'}}
        padding={{vertical: 16, horizontal: 24}}
        border="top-and-bottom"
      >
        <Box flex={{alignItems: 'center', direction: 'row', gap: 8}}>
          <Subheading>{flagPoolUI ? 'Pools' : 'Global op/asset concurrency'}</Subheading>
          {flagPoolUI ? null : <Tag>Experimental</Tag>}
        </Box>
        {onAdd ? (
          <Button icon={<Icon name="add_circle" />} onClick={() => onAdd()}>
            {flagPoolUI ? 'Add pool limit' : 'Add concurrency limit'}
          </Button>
        ) : null}
      </Box>
      {setSearch ? (
        <Box flex={{direction: 'row'}} padding={{vertical: 16, horizontal: 24}} border="bottom">
          <TextInput
            value={search || ''}
            style={{width: '30vw', minWidth: 150, maxWidth: 400}}
            placeholder={flagPoolUI ? 'Filter pools' : 'Filter concurrency keys'}
            onChange={(e: React.ChangeEvent<any>) => setSearch(e.target.value)}
          />
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
  const {flagPoolUI} = useFeatureFlags();
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
    <Dialog
      isOpen={open}
      title={flagPoolUI ? 'Add pool limit' : 'Add concurrency limit'}
      onClose={onClose}
    >
      <DialogBody>
        <Box margin={{bottom: 4}}>{flagPoolUI ? 'Pool' : 'Concurrency key'}:</Box>
        <Box margin={{bottom: 16}}>
          <TextInput
            value={keyInput || ''}
            onChange={(e) => setKeyInput(e.target.value)}
            placeholder={flagPoolUI ? 'Pool' : 'Concurrency key'}
          />
        </Box>
        <Box margin={{bottom: 4}}>
          {flagPoolUI ? 'Pool' : 'Concurrency'} limit ({minValue}-{maxValue}):
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
