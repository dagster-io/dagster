import {
  InstigationStatus,
  buildAssetGroup,
  buildInstigationState,
  buildPartitionSet,
  buildPipeline,
  buildRepositoryLocation,
  buildRepositoryMetadata,
  buildSchedule,
  buildSensor,
  buildTarget,
  buildRepository,
} from '../../graphql/types';

export const mockRepository = {
  repository: buildRepository({
    id: '343870956dd1f7d356e4ea564a099f360cf330b4',
    name: 'toys_repository',
    pipelines: [
      buildPipeline({
        id: '04c9d0aa6ac1191a86a1a456010c78d722b1eb4e',
        name: '__ASSET_JOB',
        isJob: true,
        isAssetJob: true,
        pipelineSnapshotId: '49ff60a4dbadd5bcebbd618a227714c055c74e9b',
      }),
      buildPipeline({
        id: 'f4e9f4d98ce371b60135a923188cf70eba2ae767',
        name: 'branch',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '568373150c336232cc6381746e72b50c70007f00',
      }),
      buildPipeline({
        id: '4a70048bb58120d78ccb5c07dd1a33199c92638f',
        name: 'branch_failed',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '2f3b5a3e1ffa84624fd5f7c1391b7c1f0c52de88',
      }),
      buildPipeline({
        id: '964a67440359e7aa3e634d3507ee6244632bec56',
        name: 'composition',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '9ff0cd43202505f55ceae233f6d32f589382195f',
      }),
      buildPipeline({
        id: 'ee37cb819efe9239c8c3f923dad048131f4918b9',
        name: 'df_stats_job',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '6c78672ff3c920500d1a83758e1eb7be0cf8ec07',
      }),
      buildPipeline({
        id: '6c3b1ca2f20418d443e07ec1d1f3c93a5ffd7ac3',
        name: 'dynamic',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '9893b2d21b513fd8326d33cad5127f6ae610054f',
      }),
      buildPipeline({
        id: '7ee2c407859ec47344b3234ecebb8720f1836fc6',
        name: 'error_monster_failing_job',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '650a0b1d2e615b18783880feac67816b441276b5',
      }),
      buildPipeline({
        id: '9cd2bc8439964b05d33a719e8bc54e99309f52b5',
        name: 'error_monster_passing_job',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '58587ba9860b5803be0b3ee94dc0b5bcfdf6e8d9',
      }),
      buildPipeline({
        id: 'ba49d6d36a6494fe2f288d03d62d72492ac6808d',
        name: 'fails_job',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: 'd48cdd81c79e197856b7886737b0f44a804079dc',
      }),
      buildPipeline({
        id: '2b6ab2ee559733aaf5a7ec6f4345ff4cd3aafcc0',
        name: 'hammer',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '97bc0aff9f3f33f18442eb568d0c4895f42780e2',
      }),
      buildPipeline({
        id: 'c624b82351920833a77e64772685efabf87b849e',
        name: 'hello_world_notebook_pipeline',
        isJob: false,
        isAssetJob: false,
        pipelineSnapshotId: '2bf5e7b9bdafe93423c0090a928e0240a80fe1ff',
      }),
      buildPipeline({
        id: '5733e8d0f44dc830ebb4b2708ca3b040d8d89bf3',
        name: 'log_asset',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: 'e81d385c707872156b764ee8457ea59fff6dc5ea',
      }),
      buildPipeline({
        id: '7f04867edd33611ebf73257aaaed60de47572720',
        name: 'log_file',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '308942bb930c4c1955abaf3187f2a4eaf9c747c8',
      }),
      buildPipeline({
        id: '4f45dfe35920b54ad1dab69e18007fd9e8b16bc5',
        name: 'log_s3',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '7acb7d5376ce3139998cd3d1c30ee84c6dd081d2',
      }),
      buildPipeline({
        id: 'f67e4358eb8ce761017115f3bd3cc0661460ad51',
        name: 'log_spew',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '759bbe468087f037941ea09e315da56c0e2ffc2e',
      }),
      buildPipeline({
        id: 'd80b7a96edb0789aa4416f7585387b1485b287c2',
        name: 'longitudinal',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: 'cb0c0e842f2d2ae9d29aa96bfb398485e63aeb50',
      }),
      buildPipeline({
        id: '7ef931fd50f680dfc377e78cd2ca69eac7e37c4f',
        name: 'longitudinal_no_schedule',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: 'f2e554fe22525db4dcec5ff581bb24cc3b0a025f',
      }),
      buildPipeline({
        id: 'c42481e60f0ffb1a1751bf289887b3999849cc17',
        name: 'many_events',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '35dc52a2d49542472a029e4021237d6b0164fe73',
      }),
      buildPipeline({
        id: 'a8730a18921e74d9eda86146115fee7373f5273f',
        name: 'many_events_daily',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '025f0588188b15a2b0a83938b80bb2005c01766a',
      }),
      buildPipeline({
        id: '189ff40e257421fb3e89f40d682a422588366786',
        name: 'many_events_hourly',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '389bc7201770934b4d588ce0da521fe99a5c3001',
      }),
      buildPipeline({
        id: 'faae1720f15a9f91710aba619dea43900d9c1f53',
        name: 'many_events_monthly',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: 'e17a9e445209d8a70b7809eff980e9eed327111f',
      }),
      buildPipeline({
        id: 'aba1482a323c4649725e8fe18a089c943fd1c41e',
        name: 'many_events_subset_job',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '3810bb1dba8be9abf8dc4eec5193f6ae27e12cc3',
      }),
      buildPipeline({
        id: '2ab3620a41d9f88c64d0c4d8456d0972a394de89',
        name: 'many_events_weekly',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: 'b0fe6a1258dd83616b0289cd9c9ff4cd28c6f98a',
      }),
      buildPipeline({
        id: '2a8313af150af2c7081e0ccfa0569de8bd91f812',
        name: 'model',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '97b7dbfb6f9f2fd456048d30489742c3e9368c2b',
      }),
      buildPipeline({
        id: 'ec4cef2efc3a587d386994a6ea195be517c65955',
        name: 'multi_inputs_outputs',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: 'a010ab79823c2ea9f8226735c72dcabdc24b0092',
      }),
      buildPipeline({
        id: '06acd7cee1f9dd1b5932fd4cf2452a2ff1097d3a',
        name: 'retry',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '1930376b96846ce7a7b25c871c813d7b42aaafa9',
      }),
      buildPipeline({
        id: 'e0efa1835695902fc2c1b73cde61eeec2d1b872c',
        name: 'sleepy',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '383333ddaa0317ee4ff17a3099892602c748ee40',
      }),
      buildPipeline({
        id: 'd7f5fd2cc24dc0a293cfa9e08c906b1412b1e08b',
        name: 'status_job',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: 'ae480898abd9d299baa5fdbc517e75196b7c365e',
      }),
      buildPipeline({
        id: '15eb549832b9c7548a636efda293afffd2dec98d',
        name: 'succeeds_job',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '6398711483a448398bce2b84f1ed3d9426bac5f7',
      }),
      buildPipeline({
        id: '426045161087b5e8fcb574298120031f9d123270',
        name: 'unreliable',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '20c150e1346acf5d286fbc422a3e4624a682eaa3',
      }),
      buildPipeline({
        id: 'efd0f68c921f573196d1db585e0d6d5b8d521ba0',
        name: 'unreliable_job_no_schedule',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: 'e8ecf99043fe3cd028fe2e8aafcf43825f617c81',
      }),
      buildPipeline({
        id: 'ab37f9702c04cb8994b1049fbfab01bb2b9aa632',
        name: 'with_metadata',
        isJob: true,
        isAssetJob: false,
        pipelineSnapshotId: '65e8ff34807bfa135eed94521674788646548cf2',
      }),
    ],
    schedules: [
      buildSchedule({
        id: 'dd62db7c3796270bd1a7df9f66669cb7d705d753',
        cronSchedule: '0 0 * * *',
        executionTimezone: 'US/Pacific',
        mode: 'default',
        name: 'longitudinal_schedule',
        pipelineName: 'longitudinal',
        scheduleState: buildInstigationState({
          id: '83520450a419ab4abe71e927ea6884a5a1763e02',
          selectorId: '961c5e90078ffcc98f80bfff921d224d9372584c',
          status: InstigationStatus.RUNNING,
        }),
      }),
      buildSchedule({
        id: '7dd25324a1b300bc1d708ec0601fa04db4a3193f',
        cronSchedule: '0 0 * * *',
        executionTimezone: 'US/Pacific',
        mode: 'default',
        name: 'many_events_daily_schedule',
        pipelineName: 'many_events_daily',
        scheduleState: buildInstigationState({
          id: '8e6033165ff805833501a0b57252abd05e411e24',
          selectorId: 'dd67d4f142832380879652783bbde38582ba3f18',
          status: InstigationStatus.RUNNING,
        }),
      }),
      buildSchedule({
        id: 'a50b45795084a665a749a82261321ed4b78de261',
        cronSchedule: '0 * * * *',
        executionTimezone: 'US/Pacific',
        mode: 'default',
        name: 'many_events_hourly_schedule',
        pipelineName: 'many_events_hourly',
        scheduleState: buildInstigationState({
          id: '12cde9267c6b0b9d797a14dbae5ac377e43deea9',
          selectorId: 'c9289ad3243f0afdd28b9d4f4d8ac583a80d9b5c',
          status: InstigationStatus.RUNNING,
        }),
      }),
      buildSchedule({
        id: 'bb0f48e0cb32866888e85334b8f3b158282bd530',
        cronSchedule: '0 0 1 * *',
        executionTimezone: 'US/Pacific',
        mode: 'default',
        name: 'many_events_monthly_schedule',
        pipelineName: 'many_events_monthly',
        scheduleState: buildInstigationState({
          id: '833b454fcca7f1ce95a5de24fed2ce1adc3af507',
          selectorId: '333126d759b37be434cb4365fd449570e363a2ae',
          status: InstigationStatus.RUNNING,
        }),
      }),
      buildSchedule({
        id: '56c794dbf06f169acb4b0a5b9737e20710c39dd3',
        cronSchedule: '0 0 * * 0',
        executionTimezone: 'US/Pacific',
        mode: 'default',
        name: 'many_events_weekly_schedule',
        pipelineName: 'many_events_weekly',
        scheduleState: buildInstigationState({
          id: '9301ae4bb255bfa34fa32fd4fd18ac12a83256bf',
          selectorId: 'de0b0739480731543bd5705e7d150e51a318287e',
          status: InstigationStatus.RUNNING,
        }),
      }),
      buildSchedule({
        id: '9c4fc8b26e7b514d2ceb40c91efb37fca7914cf3',
        cronSchedule: '0 0 * * 0',
        executionTimezone: 'US/Pacific',
        mode: 'default',
        name: 'unreliable_schedule',
        pipelineName: 'unreliable',
        scheduleState: buildInstigationState({
          __typename: 'InstigationState',
          id: 'd937b9de109569edf509922475935afa8473e7e5',
          selectorId: '017d8fa0e5b6a759105830b7dbfab1f27f4501c2',
          status: InstigationStatus.RUNNING,
        }),
      }),
    ],
    sensors: [
      buildSensor({
        id: '61ef822468c1fe6e543ffc06dc2290b5811225b6',
        jobOriginId: '61ef822468c1fe6e543ffc06dc2290b5811225b6',
        name: 'built_in_slack_on_run_failure_sensor',
        targets: [],
        sensorState: buildInstigationState({
          id: '61ef822468c1fe6e543ffc06dc2290b5811225b6',
          selectorId: '93f58d9e63bb03a9aaee02eb17ea5c6506a9f414',
          status: InstigationStatus.STOPPED,
        }),
      }),
      buildSensor({
        id: '173a849e47e9e27f893d556c6cfbd143d784d3b1',
        jobOriginId: '173a849e47e9e27f893d556c6cfbd143d784d3b1',
        name: 'cross_repo_job_sensor',
        targets: [
          buildTarget({
            mode: 'default',
            pipelineName: 'status_job',
          }),
        ],
        sensorState: buildInstigationState({
          id: '173a849e47e9e27f893d556c6cfbd143d784d3b1',
          selectorId: '5262ea225d59417fb603985c2cc70d547ba7da53',
          status: InstigationStatus.STOPPED,
        }),
      }),
      buildSensor({
        id: 'c88c9cf57954aa0ba98cfb0d7823e040ba39953e',
        jobOriginId: 'c88c9cf57954aa0ba98cfb0d7823e040ba39953e',
        name: 'cross_repo_sensor',
        targets: [
          buildTarget({
            mode: 'default',
            pipelineName: 'status_job',
          }),
        ],
        sensorState: buildInstigationState({
          id: 'f18d6ccdb6cd218b969c34f767788221039abdaa',
          selectorId: '0f91d2a0e242ac71bfbdb37f6f0172c4c29963d0',
          status: InstigationStatus.RUNNING,
        }),
      }),
      buildSensor({
        id: 'acb6fa8535f15a0624e8f4463a08c5dc7703833b',
        jobOriginId: 'acb6fa8535f15a0624e8f4463a08c5dc7703833b',
        name: 'cross_repo_success_job_sensor',
        targets: [
          buildTarget({
            mode: 'default',
            pipelineName: 'status_job',
          }),
        ],
        sensorState: buildInstigationState({
          id: 'acb6fa8535f15a0624e8f4463a08c5dc7703833b',
          selectorId: 'c77fa4e955b5989ecb98943d3dd6e059abe4f1ef',
          status: InstigationStatus.STOPPED,
        }),
      }),
      buildSensor({
        id: '3dee33d4123e5c55e07bd94a88f16b822b71ef1d',
        jobOriginId: '3dee33d4123e5c55e07bd94a88f16b822b71ef1d',
        name: 'custom_slack_on_job_failure',
        targets: [],
        sensorState: buildInstigationState({
          id: '10c32cd4512560b6144df9148bfc95b278496964',
          selectorId: 'd869837a53139fdc2a021b5f16fdd6bb0ae9191c',
          status: InstigationStatus.RUNNING,
        }),
      }),
      buildSensor({
        id: '75b15df46bf801a3df59a4adc9d77617cfb06273',
        jobOriginId: '75b15df46bf801a3df59a4adc9d77617cfb06273',
        name: 'fails_sensor',
        targets: [
          buildTarget({
            mode: 'default',
            pipelineName: 'status_job',
          }),
        ],
        sensorState: buildInstigationState({
          id: '2a5cffbc09fec15eb0fd130937b6bfb8155e7505',
          selectorId: '903d38ec450b93dd3a1bfa160c97ff7c0e2b0bcd',
          status: InstigationStatus.RUNNING,
        }),
      }),
      buildSensor({
        id: '83df44249d8826f0446ce59b8f09d78bc6311248',
        jobOriginId: '83df44249d8826f0446ce59b8f09d78bc6311248',
        name: 'instance_success_sensor',
        targets: [
          buildTarget({
            mode: 'default',
            pipelineName: 'status_job',
          }),
        ],
        sensorState: buildInstigationState({
          id: '83df44249d8826f0446ce59b8f09d78bc6311248',
          selectorId: '47343410d73eeb5072a4c29913a25ea088aa4428',
          status: InstigationStatus.STOPPED,
        }),
      }),
      buildSensor({
        id: '56ec6e55e9965eb8f05e6e0bbbca7c1ea51a2409',
        jobOriginId: '56ec6e55e9965eb8f05e6e0bbbca7c1ea51a2409',
        name: 'return_multi_run_request_success_sensor',
        targets: [
          buildTarget({
            mode: 'default',
            pipelineName: 'status_job',
          }),
        ],
        sensorState: buildInstigationState({
          id: '56ec6e55e9965eb8f05e6e0bbbca7c1ea51a2409',
          selectorId: 'c058f70dd1340ae0797a38996c45d3738858e6bb',
          status: InstigationStatus.STOPPED,
        }),
      }),
      buildSensor({
        id: '8fb73d8035db268c22763679d727b78f66836de6',
        jobOriginId: '8fb73d8035db268c22763679d727b78f66836de6',
        name: 'return_run_request_succeeds_sensor',
        targets: [
          buildTarget({
            mode: 'default',
            pipelineName: 'status_job',
          }),
        ],
        sensorState: buildInstigationState({
          id: 'a6c1db7c94a800b8bf96a3719e92fac5d7a1ec60',
          selectorId: '88bc231d9966ab0f306cc2c7e03fa24f6617a49a',
          status: InstigationStatus.RUNNING,
        }),
      }),
      buildSensor({
        id: '39aa6a63bbe8ca7724535c4ac3d0d39273544f46',
        jobOriginId: '39aa6a63bbe8ca7724535c4ac3d0d39273544f46',
        name: 'success_sensor_with_pipeline_run_reaction',
        targets: [],
        sensorState: buildInstigationState({
          id: 'ec1d630f04d27692288145880ebac038c8ce8932',
          selectorId: '0cf64b56d6b56cfd8711636a5298392deb9ebb6b',
          status: InstigationStatus.RUNNING,
        }),
      }),
      buildSensor({
        id: '352db1e385e427ecb20c775e39945f373a79abe8',
        jobOriginId: '352db1e385e427ecb20c775e39945f373a79abe8',
        name: 'toy_asset_sensor',
        targets: [
          buildTarget({
            mode: 'default',
            pipelineName: 'log_asset',
          }),
        ],
        sensorState: buildInstigationState({
          id: '352db1e385e427ecb20c775e39945f373a79abe8',
          selectorId: '45e0f055a5b60d8152ba325e33bf1d08c64daf9a',
          status: InstigationStatus.STOPPED,
        }),
      }),
      buildSensor({
        id: '8c8110e095e45239948246b18f9c66def47a2a11',
        jobOriginId: '8c8110e095e45239948246b18f9c66def47a2a11',
        name: 'toy_file_sensor',
        targets: [
          buildTarget({
            mode: 'default',
            pipelineName: 'log_file',
          }),
        ],
        sensorState: buildInstigationState({
          id: 'abe2076b4d21ada25109611e1d8222ed6954f618',
          selectorId: '74d1608c45491f1304a74d3dc054b9c15fbf50af',
          status: InstigationStatus.STOPPED,
        }),
      }),
      buildSensor({
        id: '2bb45dc194ee73836169ddea0f62a7967392b473',
        jobOriginId: '2bb45dc194ee73836169ddea0f62a7967392b473',
        name: 'toy_s3_sensor',
        targets: [
          buildTarget({
            mode: 'default',
            pipelineName: 'log_s3',
          }),
        ],
        sensorState: buildInstigationState({
          id: 'c2cb0bc5e6806f3f80e9e758a2641f4bd1b29a0b',
          selectorId: '19edccc5beae340e591534fe0b5b490def722c47',
          status: InstigationStatus.STOPPED,
        }),
      }),
      buildSensor({
        id: 'dd7af1fbb7186a14f1f9eaa9a46e6eb612af0c11',
        jobOriginId: 'dd7af1fbb7186a14f1f9eaa9a46e6eb612af0c11',
        name: 'yield_multi_run_request_success_sensor',
        targets: [
          buildTarget({
            mode: 'default',
            pipelineName: 'status_job',
          }),
        ],
        sensorState: buildInstigationState({
          id: 'dd7af1fbb7186a14f1f9eaa9a46e6eb612af0c11',
          selectorId: '7e279ac922efd0e533c1d209c1266607d574e179',
          status: InstigationStatus.STOPPED,
        }),
      }),
      buildSensor({
        id: 'f18ca876eb4137bacf98278ba20666ee204f5ab5',
        jobOriginId: 'f18ca876eb4137bacf98278ba20666ee204f5ab5',
        name: 'yield_run_request_succeeds_sensor',
        targets: [
          buildTarget({
            mode: 'default',
            pipelineName: 'status_job',
          }),
        ],
        sensorState: buildInstigationState({
          id: 'f18ca876eb4137bacf98278ba20666ee204f5ab5',
          selectorId: 'd21160a67d3a79ef27941093b3736bf2dabf8f11',
          status: InstigationStatus.STOPPED,
        }),
      }),
    ],
    partitionSets: [
      buildPartitionSet({
        id: '988124fc4111df0d0ffb454fddcab10e71518179',
        mode: 'default',
        pipelineName: 'longitudinal',
      }),
      buildPartitionSet({
        id: '072e1271e486e9d5ef0a1d76f4ee1f1b925c331f',
        mode: 'default',
        pipelineName: 'many_events_daily',
      }),
      buildPartitionSet({
        id: '35f43ee143de91c7cbfb453c9369c1d46139c9e3',
        mode: 'default',
        pipelineName: 'many_events_hourly',
      }),
      buildPartitionSet({
        id: '13021ff1320ec888cbbfcbf7ab0b6d6456d29944',
        mode: 'default',
        pipelineName: 'many_events_monthly',
      }),
      buildPartitionSet({
        id: 'a29e2526e9a173a6385fbafb9d625f549f258732',
        mode: 'default',
        pipelineName: 'many_events_weekly',
      }),
      buildPartitionSet({
        id: '3895c93ff44f3d39830d681f174857d81f560787',
        mode: 'default',
        pipelineName: 'unreliable',
      }),
    ],
    assetGroups: [
      buildAssetGroup({
        groupName: 'default',
      }),
    ],
    location: buildRepositoryLocation({
      id: 'dagster_test.toys.repo',
      name: 'dagster_test.toys.repo',
    }),
    displayMetadata: [
      buildRepositoryMetadata({
        key: 'module_name',
        value: 'dagster_test.toys.repo',
      }),
    ],
  }),
  repositoryLocation: buildRepositoryLocation({
    id: 'dagster_test.toys.repo',
    isReloadSupported: true,
    serverId: 'bfac18f3-5dba-464b-a563-3b89b775dd2f',
    name: 'dagster_test.toys.repo',
    repositories: [
      buildRepository({
        id: '65268e0e2e29cebb4718e536b9a925670e724413',
        name: 'asset_groups_repository',
        pipelines: [
          buildPipeline({
            id: 'fd67803db7d4ea99c7384ff198541f3558247e9b',
            name: '__ASSET_JOB',
            isJob: true,
            isAssetJob: true,
            pipelineSnapshotId: '1e38f208e7762cac52e2a1f3f9035eeb50c0f45f',
          }),
        ],
        schedules: [],
        sensors: [],
        partitionSets: [],
        assetGroups: [
          buildAssetGroup({
            groupName: 'water',
          }),
          buildAssetGroup({
            groupName: 'earth',
          }),
          buildAssetGroup({
            groupName: 'air',
          }),
        ],
        location: buildRepositoryLocation({
          id: 'dagster_test.toys.repo',
          name: 'dagster_test.toys.repo',
        }),
        displayMetadata: [
          buildRepositoryMetadata({
            key: 'module_name',
            value: 'dagster_test.toys.repo',
          }),
        ],
      }),
      buildRepository({
        id: 'de0a911bbfa12a1320a7676b0418bcb18c19b528',
        name: 'upstream_assets_repository',
        pipelines: [
          buildPipeline({
            id: 'f90fcb8023c8a90e210aed87d01182891b106009',
            name: '__ASSET_JOB',
            isJob: true,
            isAssetJob: true,
            pipelineSnapshotId: '74a76b09c8c49082368a70e696a1cbc3b0d1ea5a',
          }),
        ],
        schedules: [],
        sensors: [],
        partitionSets: [],
        assetGroups: [
          buildAssetGroup({
            groupName: 'default',
          }),
        ],
        location: buildRepositoryLocation({
          id: 'dagster_test.toys.repo',
          name: 'dagster_test.toys.repo',
        }),
        displayMetadata: [
          buildRepositoryMetadata({
            key: 'module_name',
            value: 'dagster_test.toys.repo',
          }),
        ],
      }),
      buildRepository({
        id: '019a28b1449b020160560c0f2dffa7f2ae5af51d',
        name: 'graph_backed_asset_repository',
        pipelines: [
          buildPipeline({
            id: 'e09c7774e950144a09a5902fbc13162cf9d68906',
            name: '__ASSET_JOB',
            isJob: true,
            isAssetJob: true,
            pipelineSnapshotId: '0182504f9818df49f598fe6cefa0f4343101ac4b',
          }),
        ],
        schedules: [],
        sensors: [],
        partitionSets: [],
        assetGroups: [
          buildAssetGroup({
            groupName: 'hello_world_group',
          }),
        ],
        location: buildRepositoryLocation({
          id: 'dagster_test.toys.repo',
          name: 'dagster_test.toys.repo',
        }),
        displayMetadata: [
          buildRepositoryMetadata({
            key: 'module_name',
            value: 'dagster_test.toys.repo',
          }),
        ],
      }),
      buildRepository({
        id: '05276aaa9c09dbd1c5528c3ee0c32bfc6dabfa9f',
        name: 'conditional_assets_repository',
        pipelines: [
          buildPipeline({
            id: 'b427188e7eb5fd71736de4f750c925f6a33aee40',
            name: '__ASSET_JOB',
            isJob: true,
            isAssetJob: true,
            pipelineSnapshotId: '49d5f6247fdbe034c8dd1d976186a1dc193db708',
          }),
          buildPipeline({
            id: 'e67b7e1052c1dcd28f17aa03ace57e2baa193c35',
            name: 'success_job',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '18eb6dd46d9b5298a38b8b915e568c4c02659e9c',
          }),
        ],
        schedules: [],
        sensors: [
          buildSensor({
            id: '57761896737a87744fe46d94a0099c6da531618a',
            jobOriginId: '57761896737a87744fe46d94a0099c6da531618a',
            name: 'may_not_materialize_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'success_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: '57761896737a87744fe46d94a0099c6da531618a',
              selectorId: '1dc4d9073358241ed38dcdcae216f93eae73af85',
              status: InstigationStatus.STOPPED,
            }),
          }),
        ],
        partitionSets: [],
        assetGroups: [
          buildAssetGroup({
            groupName: 'default',
          }),
        ],
        location: buildRepositoryLocation({
          id: 'dagster_test.toys.repo',
          name: 'dagster_test.toys.repo',
        }),
        displayMetadata: [
          buildRepositoryMetadata({
            key: 'module_name',
            value: 'dagster_test.toys.repo',
          }),
        ],
      }),
      buildRepository({
        id: '343870956dd1f7d356e4ea564a099f360cf330b4',
        name: 'toys_repository',
        pipelines: [
          buildPipeline({
            id: '04c9d0aa6ac1191a86a1a456010c78d722b1eb4e',
            name: '__ASSET_JOB',
            isJob: true,
            isAssetJob: true,
            pipelineSnapshotId: '49ff60a4dbadd5bcebbd618a227714c055c74e9b',
          }),
          buildPipeline({
            id: 'f4e9f4d98ce371b60135a923188cf70eba2ae767',
            name: 'branch',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '568373150c336232cc6381746e72b50c70007f00',
          }),
          buildPipeline({
            id: '4a70048bb58120d78ccb5c07dd1a33199c92638f',
            name: 'branch_failed',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '2f3b5a3e1ffa84624fd5f7c1391b7c1f0c52de88',
          }),
          buildPipeline({
            id: '964a67440359e7aa3e634d3507ee6244632bec56',
            name: 'composition',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '9ff0cd43202505f55ceae233f6d32f589382195f',
          }),
          buildPipeline({
            id: 'ee37cb819efe9239c8c3f923dad048131f4918b9',
            name: 'df_stats_job',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '6c78672ff3c920500d1a83758e1eb7be0cf8ec07',
          }),
          buildPipeline({
            id: '6c3b1ca2f20418d443e07ec1d1f3c93a5ffd7ac3',
            name: 'dynamic',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '9893b2d21b513fd8326d33cad5127f6ae610054f',
          }),
          buildPipeline({
            id: '7ee2c407859ec47344b3234ecebb8720f1836fc6',
            name: 'error_monster_failing_job',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '650a0b1d2e615b18783880feac67816b441276b5',
          }),
          buildPipeline({
            id: '9cd2bc8439964b05d33a719e8bc54e99309f52b5',
            name: 'error_monster_passing_job',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '58587ba9860b5803be0b3ee94dc0b5bcfdf6e8d9',
          }),
          buildPipeline({
            id: 'ba49d6d36a6494fe2f288d03d62d72492ac6808d',
            name: 'fails_job',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: 'd48cdd81c79e197856b7886737b0f44a804079dc',
          }),
          buildPipeline({
            id: '2b6ab2ee559733aaf5a7ec6f4345ff4cd3aafcc0',
            name: 'hammer',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '97bc0aff9f3f33f18442eb568d0c4895f42780e2',
          }),
          buildPipeline({
            id: 'c624b82351920833a77e64772685efabf87b849e',
            name: 'hello_world_notebook_pipeline',
            isJob: false,
            isAssetJob: false,
            pipelineSnapshotId: '2bf5e7b9bdafe93423c0090a928e0240a80fe1ff',
          }),
          buildPipeline({
            id: '5733e8d0f44dc830ebb4b2708ca3b040d8d89bf3',
            name: 'log_asset',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: 'e81d385c707872156b764ee8457ea59fff6dc5ea',
          }),
          buildPipeline({
            id: '7f04867edd33611ebf73257aaaed60de47572720',
            name: 'log_file',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '308942bb930c4c1955abaf3187f2a4eaf9c747c8',
          }),
          buildPipeline({
            id: '4f45dfe35920b54ad1dab69e18007fd9e8b16bc5',
            name: 'log_s3',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '7acb7d5376ce3139998cd3d1c30ee84c6dd081d2',
          }),
          buildPipeline({
            id: 'f67e4358eb8ce761017115f3bd3cc0661460ad51',
            name: 'log_spew',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '759bbe468087f037941ea09e315da56c0e2ffc2e',
          }),
          buildPipeline({
            id: 'd80b7a96edb0789aa4416f7585387b1485b287c2',
            name: 'longitudinal',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: 'cb0c0e842f2d2ae9d29aa96bfb398485e63aeb50',
          }),
          buildPipeline({
            id: '7ef931fd50f680dfc377e78cd2ca69eac7e37c4f',
            name: 'longitudinal_no_schedule',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: 'f2e554fe22525db4dcec5ff581bb24cc3b0a025f',
          }),
          buildPipeline({
            id: 'c42481e60f0ffb1a1751bf289887b3999849cc17',
            name: 'many_events',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '35dc52a2d49542472a029e4021237d6b0164fe73',
          }),
          buildPipeline({
            id: 'a8730a18921e74d9eda86146115fee7373f5273f',
            name: 'many_events_daily',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '025f0588188b15a2b0a83938b80bb2005c01766a',
          }),
          buildPipeline({
            id: '189ff40e257421fb3e89f40d682a422588366786',
            name: 'many_events_hourly',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '389bc7201770934b4d588ce0da521fe99a5c3001',
          }),
          buildPipeline({
            id: 'faae1720f15a9f91710aba619dea43900d9c1f53',
            name: 'many_events_monthly',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: 'e17a9e445209d8a70b7809eff980e9eed327111f',
          }),
          buildPipeline({
            id: 'aba1482a323c4649725e8fe18a089c943fd1c41e',
            name: 'many_events_subset_job',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '3810bb1dba8be9abf8dc4eec5193f6ae27e12cc3',
          }),
          buildPipeline({
            id: '2ab3620a41d9f88c64d0c4d8456d0972a394de89',
            name: 'many_events_weekly',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: 'b0fe6a1258dd83616b0289cd9c9ff4cd28c6f98a',
          }),
          buildPipeline({
            id: '2a8313af150af2c7081e0ccfa0569de8bd91f812',
            name: 'model',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '97b7dbfb6f9f2fd456048d30489742c3e9368c2b',
          }),
          buildPipeline({
            id: 'ec4cef2efc3a587d386994a6ea195be517c65955',
            name: 'multi_inputs_outputs',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: 'a010ab79823c2ea9f8226735c72dcabdc24b0092',
          }),
          buildPipeline({
            id: '06acd7cee1f9dd1b5932fd4cf2452a2ff1097d3a',
            name: 'retry',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '1930376b96846ce7a7b25c871c813d7b42aaafa9',
          }),
          buildPipeline({
            id: 'e0efa1835695902fc2c1b73cde61eeec2d1b872c',
            name: 'sleepy',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '383333ddaa0317ee4ff17a3099892602c748ee40',
          }),
          buildPipeline({
            id: 'd7f5fd2cc24dc0a293cfa9e08c906b1412b1e08b',
            name: 'status_job',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: 'ae480898abd9d299baa5fdbc517e75196b7c365e',
          }),
          buildPipeline({
            id: '15eb549832b9c7548a636efda293afffd2dec98d',
            name: 'succeeds_job',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '6398711483a448398bce2b84f1ed3d9426bac5f7',
          }),
          buildPipeline({
            id: '426045161087b5e8fcb574298120031f9d123270',
            name: 'unreliable',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '20c150e1346acf5d286fbc422a3e4624a682eaa3',
          }),
          buildPipeline({
            id: 'efd0f68c921f573196d1db585e0d6d5b8d521ba0',
            name: 'unreliable_job_no_schedule',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: 'e8ecf99043fe3cd028fe2e8aafcf43825f617c81',
          }),
          buildPipeline({
            id: 'ab37f9702c04cb8994b1049fbfab01bb2b9aa632',
            name: 'with_metadata',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '65e8ff34807bfa135eed94521674788646548cf2',
          }),
        ],
        schedules: [
          buildSchedule({
            id: 'dd62db7c3796270bd1a7df9f66669cb7d705d753',
            cronSchedule: '0 0 * * *',
            executionTimezone: 'US/Pacific',
            mode: 'default',
            name: 'longitudinal_schedule',
            pipelineName: 'longitudinal',
            scheduleState: buildInstigationState({
              id: '83520450a419ab4abe71e927ea6884a5a1763e02',
              selectorId: '961c5e90078ffcc98f80bfff921d224d9372584c',
              status: InstigationStatus.RUNNING,
            }),
          }),
          buildSchedule({
            id: '7dd25324a1b300bc1d708ec0601fa04db4a3193f',
            cronSchedule: '0 0 * * *',
            executionTimezone: 'US/Pacific',
            mode: 'default',
            name: 'many_events_daily_schedule',
            pipelineName: 'many_events_daily',
            scheduleState: buildInstigationState({
              id: '8e6033165ff805833501a0b57252abd05e411e24',
              selectorId: 'dd67d4f142832380879652783bbde38582ba3f18',
              status: InstigationStatus.RUNNING,
            }),
          }),
          buildSchedule({
            id: 'a50b45795084a665a749a82261321ed4b78de261',
            cronSchedule: '0 * * * *',
            executionTimezone: 'US/Pacific',
            mode: 'default',
            name: 'many_events_hourly_schedule',
            pipelineName: 'many_events_hourly',
            scheduleState: buildInstigationState({
              id: '12cde9267c6b0b9d797a14dbae5ac377e43deea9',
              selectorId: 'c9289ad3243f0afdd28b9d4f4d8ac583a80d9b5c',
              status: InstigationStatus.RUNNING,
            }),
          }),
          buildSchedule({
            id: 'bb0f48e0cb32866888e85334b8f3b158282bd530',
            cronSchedule: '0 0 1 * *',
            executionTimezone: 'US/Pacific',
            mode: 'default',
            name: 'many_events_monthly_schedule',
            pipelineName: 'many_events_monthly',
            scheduleState: buildInstigationState({
              id: '833b454fcca7f1ce95a5de24fed2ce1adc3af507',
              selectorId: '333126d759b37be434cb4365fd449570e363a2ae',
              status: InstigationStatus.RUNNING,
            }),
          }),
          buildSchedule({
            id: '56c794dbf06f169acb4b0a5b9737e20710c39dd3',
            cronSchedule: '0 0 * * 0',
            executionTimezone: 'US/Pacific',
            mode: 'default',
            name: 'many_events_weekly_schedule',
            pipelineName: 'many_events_weekly',
            scheduleState: buildInstigationState({
              id: '9301ae4bb255bfa34fa32fd4fd18ac12a83256bf',
              selectorId: 'de0b0739480731543bd5705e7d150e51a318287e',
              status: InstigationStatus.RUNNING,
            }),
          }),
          buildSchedule({
            id: '9c4fc8b26e7b514d2ceb40c91efb37fca7914cf3',
            cronSchedule: '0 0 * * 0',
            executionTimezone: 'US/Pacific',
            mode: 'default',
            name: 'unreliable_schedule',
            pipelineName: 'unreliable',
            scheduleState: buildInstigationState({
              id: 'd937b9de109569edf509922475935afa8473e7e5',
              selectorId: '017d8fa0e5b6a759105830b7dbfab1f27f4501c2',
              status: InstigationStatus.RUNNING,
            }),
          }),
        ],
        sensors: [
          buildSensor({
            id: '61ef822468c1fe6e543ffc06dc2290b5811225b6',
            jobOriginId: '61ef822468c1fe6e543ffc06dc2290b5811225b6',
            name: 'built_in_slack_on_run_failure_sensor',
            targets: [],
            sensorState: buildInstigationState({
              id: '61ef822468c1fe6e543ffc06dc2290b5811225b6',
              selectorId: '93f58d9e63bb03a9aaee02eb17ea5c6506a9f414',
              status: InstigationStatus.STOPPED,
            }),
          }),
          buildSensor({
            id: '173a849e47e9e27f893d556c6cfbd143d784d3b1',
            jobOriginId: '173a849e47e9e27f893d556c6cfbd143d784d3b1',
            name: 'cross_repo_job_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'status_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: '173a849e47e9e27f893d556c6cfbd143d784d3b1',
              selectorId: '5262ea225d59417fb603985c2cc70d547ba7da53',
              status: InstigationStatus.STOPPED,
            }),
          }),
          buildSensor({
            id: 'c88c9cf57954aa0ba98cfb0d7823e040ba39953e',
            jobOriginId: 'c88c9cf57954aa0ba98cfb0d7823e040ba39953e',
            name: 'cross_repo_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'status_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: 'f18d6ccdb6cd218b969c34f767788221039abdaa',
              selectorId: '0f91d2a0e242ac71bfbdb37f6f0172c4c29963d0',
              status: InstigationStatus.RUNNING,
            }),
          }),
          buildSensor({
            id: 'acb6fa8535f15a0624e8f4463a08c5dc7703833b',
            jobOriginId: 'acb6fa8535f15a0624e8f4463a08c5dc7703833b',
            name: 'cross_repo_success_job_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'status_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: 'acb6fa8535f15a0624e8f4463a08c5dc7703833b',
              selectorId: 'c77fa4e955b5989ecb98943d3dd6e059abe4f1ef',
              status: InstigationStatus.STOPPED,
            }),
          }),
          buildSensor({
            id: '3dee33d4123e5c55e07bd94a88f16b822b71ef1d',
            jobOriginId: '3dee33d4123e5c55e07bd94a88f16b822b71ef1d',
            name: 'custom_slack_on_job_failure',
            targets: [],
            sensorState: buildInstigationState({
              id: '10c32cd4512560b6144df9148bfc95b278496964',
              selectorId: 'd869837a53139fdc2a021b5f16fdd6bb0ae9191c',
              status: InstigationStatus.RUNNING,
            }),
          }),
          buildSensor({
            id: '75b15df46bf801a3df59a4adc9d77617cfb06273',
            jobOriginId: '75b15df46bf801a3df59a4adc9d77617cfb06273',
            name: 'fails_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'status_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: '2a5cffbc09fec15eb0fd130937b6bfb8155e7505',
              selectorId: '903d38ec450b93dd3a1bfa160c97ff7c0e2b0bcd',
              status: InstigationStatus.RUNNING,
            }),
          }),
          buildSensor({
            id: '83df44249d8826f0446ce59b8f09d78bc6311248',
            jobOriginId: '83df44249d8826f0446ce59b8f09d78bc6311248',
            name: 'instance_success_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'status_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: '83df44249d8826f0446ce59b8f09d78bc6311248',
              selectorId: '47343410d73eeb5072a4c29913a25ea088aa4428',
              status: InstigationStatus.STOPPED,
            }),
          }),
          buildSensor({
            id: '56ec6e55e9965eb8f05e6e0bbbca7c1ea51a2409',
            jobOriginId: '56ec6e55e9965eb8f05e6e0bbbca7c1ea51a2409',
            name: 'return_multi_run_request_success_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'status_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: '56ec6e55e9965eb8f05e6e0bbbca7c1ea51a2409',
              selectorId: 'c058f70dd1340ae0797a38996c45d3738858e6bb',
              status: InstigationStatus.STOPPED,
            }),
          }),
          buildSensor({
            id: '8fb73d8035db268c22763679d727b78f66836de6',
            jobOriginId: '8fb73d8035db268c22763679d727b78f66836de6',
            name: 'return_run_request_succeeds_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'status_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: 'a6c1db7c94a800b8bf96a3719e92fac5d7a1ec60',
              selectorId: '88bc231d9966ab0f306cc2c7e03fa24f6617a49a',
              status: InstigationStatus.RUNNING,
            }),
          }),
          buildSensor({
            id: '39aa6a63bbe8ca7724535c4ac3d0d39273544f46',
            jobOriginId: '39aa6a63bbe8ca7724535c4ac3d0d39273544f46',
            name: 'success_sensor_with_pipeline_run_reaction',
            targets: [],
            sensorState: buildInstigationState({
              id: 'ec1d630f04d27692288145880ebac038c8ce8932',
              selectorId: '0cf64b56d6b56cfd8711636a5298392deb9ebb6b',
              status: InstigationStatus.RUNNING,
            }),
          }),
          buildSensor({
            id: '352db1e385e427ecb20c775e39945f373a79abe8',
            jobOriginId: '352db1e385e427ecb20c775e39945f373a79abe8',
            name: 'toy_asset_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'log_asset',
              }),
            ],
            sensorState: buildInstigationState({
              id: '352db1e385e427ecb20c775e39945f373a79abe8',
              selectorId: '45e0f055a5b60d8152ba325e33bf1d08c64daf9a',
              status: InstigationStatus.STOPPED,
            }),
          }),
          buildSensor({
            id: '8c8110e095e45239948246b18f9c66def47a2a11',
            jobOriginId: '8c8110e095e45239948246b18f9c66def47a2a11',
            name: 'toy_file_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'log_file',
              }),
            ],
            sensorState: buildInstigationState({
              id: 'abe2076b4d21ada25109611e1d8222ed6954f618',
              selectorId: '74d1608c45491f1304a74d3dc054b9c15fbf50af',
              status: InstigationStatus.STOPPED,
            }),
          }),
          buildSensor({
            id: '2bb45dc194ee73836169ddea0f62a7967392b473',
            jobOriginId: '2bb45dc194ee73836169ddea0f62a7967392b473',
            name: 'toy_s3_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'log_s3',
              }),
            ],
            sensorState: buildInstigationState({
              id: 'c2cb0bc5e6806f3f80e9e758a2641f4bd1b29a0b',
              selectorId: '19edccc5beae340e591534fe0b5b490def722c47',
              status: InstigationStatus.STOPPED,
            }),
          }),
          buildSensor({
            id: 'dd7af1fbb7186a14f1f9eaa9a46e6eb612af0c11',
            jobOriginId: 'dd7af1fbb7186a14f1f9eaa9a46e6eb612af0c11',
            name: 'yield_multi_run_request_success_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'status_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: 'dd7af1fbb7186a14f1f9eaa9a46e6eb612af0c11',
              selectorId: '7e279ac922efd0e533c1d209c1266607d574e179',
              status: InstigationStatus.STOPPED,
            }),
          }),
          buildSensor({
            id: 'f18ca876eb4137bacf98278ba20666ee204f5ab5',
            jobOriginId: 'f18ca876eb4137bacf98278ba20666ee204f5ab5',
            name: 'yield_run_request_succeeds_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'status_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: 'f18ca876eb4137bacf98278ba20666ee204f5ab5',
              selectorId: 'd21160a67d3a79ef27941093b3736bf2dabf8f11',
              status: InstigationStatus.STOPPED,
            }),
          }),
        ],
        partitionSets: [
          buildPartitionSet({
            id: '988124fc4111df0d0ffb454fddcab10e71518179',
            mode: 'default',
            pipelineName: 'longitudinal',
          }),
          buildPartitionSet({
            id: '072e1271e486e9d5ef0a1d76f4ee1f1b925c331f',
            mode: 'default',
            pipelineName: 'many_events_daily',
          }),
          buildPartitionSet({
            id: '35f43ee143de91c7cbfb453c9369c1d46139c9e3',
            mode: 'default',
            pipelineName: 'many_events_hourly',
          }),
          buildPartitionSet({
            id: '13021ff1320ec888cbbfcbf7ab0b6d6456d29944',
            mode: 'default',
            pipelineName: 'many_events_monthly',
          }),
          buildPartitionSet({
            id: 'a29e2526e9a173a6385fbafb9d625f549f258732',
            mode: 'default',
            pipelineName: 'many_events_weekly',
          }),
          buildPartitionSet({
            id: '3895c93ff44f3d39830d681f174857d81f560787',
            mode: 'default',
            pipelineName: 'unreliable',
          }),
        ],
        assetGroups: [
          buildAssetGroup({
            groupName: 'default',
          }),
        ],
        location: buildRepositoryLocation({
          id: 'dagster_test.toys.repo',
          name: 'dagster_test.toys.repo',
        }),
        displayMetadata: [
          buildRepositoryMetadata({
            key: 'module_name',
            value: 'dagster_test.toys.repo',
          }),
        ],
      }),
      buildRepository({
        id: '00ff71b2434607dc9b23c6e9b67522199790809e',
        name: 'downstream_assets_repository2',
        pipelines: [
          buildPipeline({
            id: '0ea8aec988939798dc3b8c1249672c1344b9e0fa',
            name: '__ASSET_JOB',
            isJob: true,
            isAssetJob: true,
            pipelineSnapshotId: 'eefcb7f5c2f1ce558e8e9f1362cef431dd6183b5',
          }),
        ],
        schedules: [],
        sensors: [],
        partitionSets: [],
        assetGroups: [
          buildAssetGroup({
            groupName: 'default',
          }),
        ],
        location: buildRepositoryLocation({
          id: 'dagster_test.toys.repo',
          name: 'dagster_test.toys.repo',
        }),
        displayMetadata: [
          buildRepositoryMetadata({
            key: 'module_name',
            value: 'dagster_test.toys.repo',
          }),
        ],
      }),
      buildRepository({
        id: '051a14bd4fb8d1af8b139f74c06abc875bc6d3cf',
        name: 'downstream_assets_repository1',
        pipelines: [
          buildPipeline({
            id: '9136fd86d5ff9976c874e32f6e971253c6248e12',
            name: '__ASSET_JOB',
            isJob: true,
            isAssetJob: true,
            pipelineSnapshotId: 'a204c6d8814e5302f9b6031008f9c4650ff6b99c',
          }),
        ],
        schedules: [],
        sensors: [],
        partitionSets: [],
        assetGroups: [
          buildAssetGroup({
            groupName: 'default',
          }),
        ],
        location: buildRepositoryLocation({
          id: 'dagster_test.toys.repo',
          name: 'dagster_test.toys.repo',
        }),
        displayMetadata: [
          buildRepositoryMetadata({
            key: 'module_name',
            value: 'dagster_test.toys.repo',
          }),
        ],
      }),
      buildRepository({
        id: 'e27eda0b6689b3eaf77affc2dbfa0f4262558e0d',
        name: 'long_asset_keys_repository',
        pipelines: [
          buildPipeline({
            id: '0e8b89e04a58feec5d351b554a865fc59b73a6e0',
            name: '__ASSET_JOB',
            isJob: true,
            isAssetJob: true,
            pipelineSnapshotId: '305f9cbf284ee49d77e79c0f206b4dff057ddf44',
          }),
        ],
        schedules: [],
        sensors: [],
        partitionSets: [],
        assetGroups: [
          buildAssetGroup({
            groupName: 'default',
          }),
        ],
        location: buildRepositoryLocation({
          id: 'dagster_test.toys.repo',
          name: 'dagster_test.toys.repo',
        }),
        displayMetadata: [
          buildRepositoryMetadata({
            key: 'module_name',
            value: 'dagster_test.toys.repo',
          }),
        ],
      }),
      buildRepository({
        id: 'c4dc7a7e0967011465059afa03a6719256db2e3e',
        name: 'partitioned_asset_repository',
        pipelines: [
          buildPipeline({
            id: '2541610a6ea7215281a2ceac9880d114fcf63680',
            name: '__ASSET_JOB_0',
            isJob: true,
            isAssetJob: true,
            pipelineSnapshotId: '9f3d4115308e51b87d050ec8036b58f1912cd20c',
          }),
          buildPipeline({
            id: '2ca55e24a69d708229e8dff57f9c1170960ea2de',
            name: '__ASSET_JOB_1',
            isJob: true,
            isAssetJob: true,
            pipelineSnapshotId: '00126e0094430d4d93a74fe8b30727dd873855ce',
          }),
        ],
        schedules: [],
        sensors: [],
        partitionSets: [
          buildPartitionSet({
            id: '06b4c967d19fb450cecf90fe97c28381d7141fad',
            mode: 'default',
            pipelineName: '__ASSET_JOB_0',
          }),
          buildPartitionSet({
            id: 'f4f2ec1a85eb5e676ed30fe0663d343a7fc33b34',
            mode: 'default',
            pipelineName: '__ASSET_JOB_1',
          }),
        ],
        assetGroups: [
          buildAssetGroup({
            groupName: 'default',
          }),
        ],
        location: buildRepositoryLocation({
          id: 'dagster_test.toys.repo',
          name: 'dagster_test.toys.repo',
        }),
        displayMetadata: [
          buildRepositoryMetadata({
            key: 'module_name',
            value: 'dagster_test.toys.repo',
          }),
        ],
      }),
      buildRepository({
        id: '4b5ea59c0a80aea0316b4754fad1cc4979824847',
        name: 'assets_with_sensors_repository',
        pipelines: [
          buildPipeline({
            id: 'a6930aa603d3e8400c34010bf8fbbbd2fa39e856',
            name: '__ASSET_JOB',
            isJob: true,
            isAssetJob: true,
            pipelineSnapshotId: '4de04e6653c629070d0514cd7312abe40b4d3d45',
          }),
          buildPipeline({
            id: '2bd0009c9177905b3e2496cb132d2a4ab85d61c6',
            name: 'log_asset_sensor_job',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '8734216248fb227de44bdc1e3291fdbe96fd1ea4',
          }),
        ],
        schedules: [],
        sensors: [
          buildSensor({
            id: 'd04b7d0c2b936d6b6743ba5babdcc25614c60b97',
            jobOriginId: 'd04b7d0c2b936d6b6743ba5babdcc25614c60b97',
            name: 'asset_a_and_b_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'log_asset_sensor_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: '800e85d224d5b075c6023ce10e3683c140d297b0',
              selectorId: 'c81cc9fbe8b3f6b08761be714a5604fe416b68dc',
              status: InstigationStatus.RUNNING,
            }),
          }),
          buildSensor({
            id: 'bacfcb5eeeeb5614e371a15c22fd664e0c51a593',
            jobOriginId: 'bacfcb5eeeeb5614e371a15c22fd664e0c51a593',
            name: 'asset_c_or_d_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'log_asset_sensor_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: '522157ff2c185a9e83c56ffae79e9b4934270aa6',
              selectorId: '2f8083a709a8f1f305fd0d8aec2f98260933624b',
              status: InstigationStatus.RUNNING,
            }),
          }),
          buildSensor({
            id: 'a47bb99132a4f87be187fc22e0081887f3701554',
            jobOriginId: 'a47bb99132a4f87be187fc22e0081887f3701554',
            name: 'asset_string_and_int_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'log_asset_sensor_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: 'a47bb99132a4f87be187fc22e0081887f3701554',
              selectorId: '5fe817a5d3b2752ae37d1e0735e45bb18b91dc83',
              status: InstigationStatus.STOPPED,
            }),
          }),
          buildSensor({
            id: 'b82582e0fb5c67143d688a5cf76a549ea46bfd05',
            jobOriginId: 'b82582e0fb5c67143d688a5cf76a549ea46bfd05',
            name: 'every_fifth_materialization_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: 'log_asset_sensor_job',
              }),
            ],
            sensorState: buildInstigationState({
              id: 'b82582e0fb5c67143d688a5cf76a549ea46bfd05',
              selectorId: '3bd7c1b6d0425edc8c935dfb96d78cdbee989177',
              status: InstigationStatus.STOPPED,
            }),
          }),
          buildSensor({
            id: '4c5499d668e4e3ea6fbef325780cc02ff0ac0768',
            jobOriginId: '4c5499d668e4e3ea6fbef325780cc02ff0ac0768',
            name: 'generated_sensor',
            targets: [
              buildTarget({
                mode: 'default',
                pipelineName: '__ASSET_JOB',
              }),
            ],
            sensorState: buildInstigationState({
              id: '4c5499d668e4e3ea6fbef325780cc02ff0ac0768',
              selectorId: '3ab83ffa3a0a3e7f143670c70a1d33d756b853fb',
              status: InstigationStatus.STOPPED,
            }),
          }),
        ],
        partitionSets: [],
        assetGroups: [
          buildAssetGroup({
            groupName: 'default',
          }),
        ],
        location: buildRepositoryLocation({
          id: 'dagster_test.toys.repo',
          name: 'dagster_test.toys.repo',
        }),
        displayMetadata: [
          buildRepositoryMetadata({
            key: 'module_name',
            value: 'dagster_test.toys.repo',
          }),
        ],
      }),
      buildRepository({
        id: '617f0c23718dda0b0be27dda6682b3195e981c3e',
        name: 'big_honkin_assets_repository',
        pipelines: [
          buildPipeline({
            id: '0c583de599990e50d7837bdb193ce85f65047ce8',
            name: '__ASSET_JOB',
            isJob: true,
            isAssetJob: true,
            pipelineSnapshotId: '0331ceba4936155ad34d9301fcd766e8a97a0864',
          }),
        ],
        schedules: [],
        sensors: [],
        partitionSets: [],
        assetGroups: [
          buildAssetGroup({
            groupName: 'default',
          }),
        ],
        location: buildRepositoryLocation({
          id: 'dagster_test.toys.repo',
          name: 'dagster_test.toys.repo',
        }),
        displayMetadata: [
          buildRepositoryMetadata({
            key: 'module_name',
            value: 'dagster_test.toys.repo',
          }),
        ],
      }),
      buildRepository({
        id: 'fa2d56dc8a3d534791269585bdc97e0a6939d1b8',
        name: 'more_toys_repository',
        pipelines: [
          buildPipeline({
            id: '4804d8004d0505cd433de1608a263c1728d6997e',
            name: 'fails_job',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: 'd48cdd81c79e197856b7886737b0f44a804079dc',
          }),
          buildPipeline({
            id: '3ceb51bf7ee9f5e63966d07fa539d22ed89e3b94',
            name: 'succeeds_job',
            isJob: true,
            isAssetJob: false,
            pipelineSnapshotId: '6398711483a448398bce2b84f1ed3d9426bac5f7',
          }),
        ],
        schedules: [],
        sensors: [],
        partitionSets: [],
        assetGroups: [],
        location: buildRepositoryLocation({
          id: 'dagster_test.toys.repo',
          name: 'dagster_test.toys.repo',
        }),
        displayMetadata: [
          buildRepositoryMetadata({
            key: 'module_name',
            value: 'dagster_test.toys.repo',
          }),
        ],
      }),
    ],
  }),
};
