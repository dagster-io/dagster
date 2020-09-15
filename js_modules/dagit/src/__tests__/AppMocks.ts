import path from 'path';
import {ROOT_REPOSITORIES_QUERY} from '../DagsterRepositoryContext';
import {TYPE_EXPLORER_CONTAINER_QUERY} from '../typeexplorer/TypeExplorerContainer';
import {TYPE_LIST_CONTAINER_QUERY} from '../typeexplorer/TypeListContainer';
import {SOLIDS_ROOT_QUERY} from '../solids/SolidsRoot';
import {USED_SOLID_DETAILS_QUERY} from '../solids/SolidDetailsRoot';
import {PIPELINE_EXPLORER_ROOT_QUERY} from '../PipelineExplorerRoot';
import {SIDEBAR_TABBED_CONTAINER_SOLID_QUERY} from '../SidebarSolidContainer';
import {CachedGraphQLRequest} from './MockedApolloLinks';

import {PipelineExplorerRootQueryVariables} from '../types/PipelineExplorerRootQuery';
import {TypeExplorerContainerQueryVariables} from '../typeexplorer/types/TypeExplorerContainerQuery';
import {TypeListContainerQueryVariables} from '../typeexplorer/types/TypeListContainerQuery';
import {SidebarTabbedContainerSolidQueryVariables} from '../types/SidebarTabbedContainerSolidQuery';

export const MOCKS: CachedGraphQLRequest[] = [
  {
    name: 'ROOT_REPOSITORIES_QUERY',
    query: ROOT_REPOSITORIES_QUERY,
    variables: undefined,
    filepath: path.join(__dirname, '__data__', 'ROOT_REPOSITORIES_QUERY.json'),
  },
  {
    name: 'PIPELINE_EXPLORER_ROOT_QUERY',
    query: PIPELINE_EXPLORER_ROOT_QUERY,
    variables: {
      pipelineSelector: {
        pipelineName: 'airline_demo_ingest_pipeline',
        repositoryLocationName: '<<in_process>>',
        repositoryName: 'internal_dagit_repository',
        solidSelection: undefined,
      },
      snapshotId: undefined,
      rootHandleID: '',
      requestScopeHandleID: '',
    } as PipelineExplorerRootQueryVariables,
    filepath: path.join(__dirname, '__data__', 'PIPELINE_EXPLORER_ROOT_QUERY.json'),
  },
  {
    name: 'TYPE_EXPLORER_CONTAINER_QUERY',
    query: TYPE_EXPLORER_CONTAINER_QUERY,
    variables: {
      pipelineSelector: {
        repositoryLocationName: '<<in_process>>',
        repositoryName: 'internal_dagit_repository',
        pipelineName: 'airline_demo_ingest_pipeline',
      },
      dagsterTypeName: 'PySparkDataFrame',
    } as TypeExplorerContainerQueryVariables,
    filepath: path.join(__dirname, '__data__', 'TYPE_EXPLORER_CONTAINER_QUERY.json'),
  },
  {
    name: 'TYPE_LIST_CONTAINER_QUERY',
    query: TYPE_LIST_CONTAINER_QUERY,
    variables: {
      pipelineSelector: {
        repositoryLocationName: '<<in_process>>',
        repositoryName: 'internal_dagit_repository',
        pipelineName: 'airline_demo_ingest_pipeline',
      },
    } as TypeListContainerQueryVariables,
    filepath: path.join(__dirname, '__data__', 'TYPE_LIST_CONTAINER_QUERY.json'),
  },
  {
    name: 'SOLIDS_ROOT_QUERY',
    query: SOLIDS_ROOT_QUERY,
    variables: {
      repositorySelector: {
        repositoryLocationName: '<<in_process>>',
        repositoryName: 'internal_dagit_repository',
      },
    },
    filepath: path.join(__dirname, '__data__', 'SOLIDS_ROOT_QUERY.json'),
  },
  {
    name: 'USED_SOLIDS_DETAILS_QUERY',
    query: USED_SOLID_DETAILS_QUERY,
    variables: {
      repositorySelector: {
        repositoryLocationName: '<<in_process>>',
        repositoryName: 'internal_dagit_repository',
      },
      name: 's3_to_df',
    },
    filepath: path.join(__dirname, '__data__', 'USED_SOLID_DETAILS_QUERY.json'),
  },
  {
    name: 'SIDEBAR_TABBED_CONTAINER_SOLID_QUERY',
    query: SIDEBAR_TABBED_CONTAINER_SOLID_QUERY,
    variables: {
      selector: {
        repositoryLocationName: '<<in_process>>',
        repositoryName: 'internal_dagit_repository',
        pipelineName: 'airline_demo_ingest_pipeline',
      },
      handleID: 'download_q2_sfo_weather',
    } as SidebarTabbedContainerSolidQueryVariables,
    filepath: path.join(__dirname, '__data__', 'SIDEBAR_TABBED_CONTAINER_SOLID_QUERY.json'),
  },
];
