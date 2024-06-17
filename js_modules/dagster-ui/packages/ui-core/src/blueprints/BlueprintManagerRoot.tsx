import {gql, useMutation, useQuery} from '@apollo/client';
import {
  Alert,
  Box,
  Button,
  ButtonLink,
  Colors,
  ConfigEditorWithSchema,
  Dialog,
  DialogFooter,
  ExternalAnchorButton,
  Group,
  Heading,
  Icon,
  Page,
  PageHeader,
  SplitPanelContainer,
  Subheading,
  Table,
  Tag,
  TextInput,
} from '@dagster-io/ui-components';
import {
  ConfigSchema,
  ConfigSchema_allConfigTypes,
  ConfigSchema_allConfigTypes_CompositeConfigType_fields,
} from '@dagster-io/ui-components/src/components/configeditor/types/ConfigSchema';
import React, {useState} from 'react';
import {useParams} from 'react-router-dom';
import styled from 'styled-components';
import {v4 as uuidv4} from 'uuid';

import {
  BlueprintManagerRootQuery,
  BlueprintManagerRootQueryVariables,
  CreateBlueprintMutation,
  CreateBlueprintMutationVariables,
  UpdateBlueprintMutation,
  UpdateBlueprintMutationVariables,
} from './types/BlueprintManagerRoot.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {useTrackPageView} from '../app/analytics';
import {Blueprint, BlueprintKey} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RepositoryLink} from '../nav/RepositoryLink';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

type JsonSchema = {
  type: string;
  properties: {
    [key: string]: JsonSchema;
  };
  additionalProperties?: JsonSchema;
  description?: string;
  required?: string[];
};

const jsonSchemaToConfigSchemaInner = (
  jsonSchema: JsonSchema,
  definitions: {[name: string]: JsonSchema},
): {
  types: ConfigSchema_allConfigTypes[];
  rootKey: string;
} => {
  // merge properties and additionalProperties into a single object

  console.log(jsonSchema);

  if (jsonSchema.additionalProperties && jsonSchema.additionalProperties['$ref']) {
    const ref = jsonSchema.additionalProperties && jsonSchema.additionalProperties['$ref'];
    const inner = jsonSchemaToConfigSchemaInner(definitions[ref.split('/').pop()!], definitions);

    const rootKeyUuid = uuidv4();
    const anyTypeUuid = uuidv4();

    return {
      types: [
        {
          __typename: 'MapConfigType',
          key: rootKeyUuid,
          description: jsonSchema.description || null,
          isSelector: false,
          keyLabelName: 'key',
          typeParamKeys: [anyTypeUuid, inner.rootKey],
        },
        {
          __typename: 'RegularConfigType',
          givenName: 'Any',
          key: anyTypeUuid,
          description: '',
          isSelector: false,
          typeParamKeys: [],
        },
        ...inner.types,
      ],
      rootKey: rootKeyUuid,
    };
  }

  if (jsonSchema['$ref'] || (jsonSchema['allOf'] && jsonSchema['allOf'].length == 1)) {
    const ref = jsonSchema['$ref'] || jsonSchema['allOf'][0]['$ref'];
    return jsonSchemaToConfigSchemaInner(definitions[ref.split('/').pop()!], definitions);
  }

  const props = {...jsonSchema.properties, ...jsonSchema.additionalProperties};
  if (jsonSchema.type === 'object' && props) {
    const fieldTypesByKey = Object.entries(props).reduce(
      (accum, [key, value]) => {
        accum[key] = jsonSchemaToConfigSchemaInner(value, definitions);
        return accum;
      },
      {} as Record<string, {types: ConfigSchema_allConfigTypes[]; rootKey: string}>,
    );

    const fieldEntries = Object.entries(props).map(([key, value]) => {
      return {
        __typename: 'ConfigTypeField',
        name: key,
        description: value.description || null,
        isRequired: (jsonSchema.required || []).includes(key),
        configTypeKey: fieldTypesByKey[key]?.rootKey,
        defaultValueAsJson: null,
      };
    }) as ConfigSchema_allConfigTypes_CompositeConfigType_fields[];

    // root key (generate a random uuid)
    const rootKeyUuid = uuidv4();

    return {
      types: [
        {
          __typename: 'CompositeConfigType',
          key: rootKeyUuid,
          description: jsonSchema.description || null,
          isSelector: false,
          typeParamKeys: [],
          fields: fieldEntries,
        },
        ...Object.values(fieldTypesByKey).flatMap((x) => x.types),
      ],
      rootKey: rootKeyUuid,
    };
  } else {
    const rootKeyUuid = uuidv4();

    return {
      types: [
        {
          __typename: 'RegularConfigType',
          givenName: 'Any',
          key: rootKeyUuid,
          description: '',
          isSelector: false,
          typeParamKeys: [],
        },
      ],
      rootKey: rootKeyUuid,
    };
  }
};

const jsonSchemaToConfigSchema = (jsonSchema: any): ConfigSchema => {
  // get first object in jsonSchema.definitions
  const firstKey = jsonSchema['$ref'].split('/').pop();

  const firstValue = jsonSchema.definitions[firstKey];
  const {types, rootKey} = jsonSchemaToConfigSchemaInner(firstValue, jsonSchema.definitions);

  return {
    __typename: 'ConfigSchema',
    rootConfigType: {
      __typename: 'CompositeConfigType',
      key: rootKey,
    },
    allConfigTypes: types,
  };
};

interface Props {
  repoAddress: RepoAddress;
}

const EditBlueprintDialog = ({
  isOpen,
  onClose,
  configSchema,
  config,
  setConfig,
  title,
  onSave,
  loading,
  createdPRUrl,
  name,
  setName,
  canSetName,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  configSchema: ConfigSchema | null;
  name: string;
  setName: (name: string) => void;
  canSetName: boolean;
  config: string;
  setConfig: (config: string) => void;
  title: string;
  createdPRUrl: string | null;
  loading: boolean;
}) => {
  return (
    <Dialog
      isOpen={isOpen}
      title={title}
      onClose={onClose}
      style={{maxWidth: '90%', minWidth: '70%', width: 1000}}
    >
      <Box flex={{direction: 'column', gap: 4}} margin={{horizontal: 32, top: 16, bottom: 24}}>
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <FormLabel htmlFor="key-name" style={{lineHeight: '16px'}}>
            Name
          </FormLabel>
        </Box>
        <TextInput
          id="key-name"
          placeholder="my_blueprint_name"
          value={name}
          disabled={!canSetName}
          onChange={(e) => setName(e.target.value)}
          style={{width: '100%'}}
        />
      </Box>
      <ConfigEditorWithSchema
        onConfigChange={setConfig}
        config={config}
        configSchema={configSchema}
        isLoading={false}
        identifier="foo"
      />
      <DialogFooter topBorder>
        <Button intent="none" onClick={onClose} disabled={loading}>
          {createdPRUrl ? 'Close' : 'Cancel'}
        </Button>
        {createdPRUrl ? (
          <ExternalAnchorButton
            intent="primary"
            href={createdPRUrl}
            icon={<Icon name="github" />}
            rightIcon={<Icon name="open_in_new" />}
          >
            Open pull request
          </ExternalAnchorButton>
        ) : (
          <Button intent="primary" onClick={onSave} icon={<Icon name="github" />} loading={loading}>
            Create pull request
          </Button>
        )}
      </DialogFooter>
    </Dialog>
  );
};

export const BlueprintManagerRoot = (props: Props) => {
  useTrackPageView();

  const {repoAddress} = props;
  const {blueprintManagerName} = useParams<{blueprintManagerName: string}>();

  const [config, setConfig] = useState<string>('');
  const [inputName, setInputName] = useState<string>('');
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editorTarget, setEditorTarget] = useState<BlueprintKey | null>(null);

  useDocumentTitle(`Blueprint Manager: ${blueprintManagerName}`);

  const blueprintManagerSelector = {
    ...repoAddressToSelector(repoAddress),
    blueprintManagerName,
  };
  const queryResult = useQuery<BlueprintManagerRootQuery, BlueprintManagerRootQueryVariables>(
    BLUEPRINT_MANAGER_ROOT_QUERY,
    {
      variables: {
        blueprintManagerSelector,
      },
    },
  );

  const [createBlueprint, createLoading] = useMutation<
    CreateBlueprintMutation,
    CreateBlueprintMutationVariables
  >(CREATE_BLUEPRINT_MUTATION);
  const [updateBlueprint, updateLoading] = useMutation<
    UpdateBlueprintMutation,
    UpdateBlueprintMutationVariables
  >(UPDATE_BLUEPRINT_MUTATION);

  const [createdPRUrl, setCreatedPRUrl] = useState<string | null>(null);

  const blueprintManager =
    queryResult.data?.blueprintManagerOrError.__typename === 'BlueprintManager'
      ? queryResult.data.blueprintManagerOrError
      : null;

  const jsonSchemaConfigSchema = React.useMemo(() => {
    if (!blueprintManager?.schema) {
      return null;
    }

    const jsonSchema = JSON.parse(blueprintManager.schema.schema);
    return jsonSchemaToConfigSchema(jsonSchema);
  }, [blueprintManager?.schema]);

  const openEditorForBlueprint = (blueprint: Blueprint) => {
    setConfig(JSON.parse(blueprint.blob.value));
    setCreatedPRUrl(null);
    setEditorTarget(blueprint.key);
    setIsEditorOpen(true);
  };

  const openEditorForNewBlueprint = () => {
    setConfig('');
    setCreatedPRUrl(null);
    setEditorTarget(null);
    setIsEditorOpen(true);
  };

  const saveConfig = async () => {
    //setIsEditorOpen(false);

    if (!editorTarget) {
      const result = await createBlueprint({
        variables: {
          blueprintManagerSelector,
          blob: config,
          identifierWithinManager: `${inputName}.yaml`,
        },
      });
      setCreatedPRUrl(result.data?.createBlueprint || null);
    } else {
      const result = await updateBlueprint({
        variables: {
          blueprintManagerSelector,
          blob: config,
          identifierWithinManager: editorTarget?.identifierWithinManager.split(':')[0],
        },
      });
      setCreatedPRUrl(result.data?.updateBlueprint || null);
    }
  };

  return (
    <Page style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader
        title={<Heading>{blueprintManager?.name}</Heading>}
        tags={
          <Tag icon="add_circle">
            BlueprintManager in <RepositoryLink repoAddress={repoAddress} />
          </Tag>
        }
      />
      <Loading queryResult={queryResult} allowStaleData={true}>
        {({blueprintManagerOrError}) => {
          if (blueprintManagerOrError.__typename !== 'BlueprintManager') {
            let message: string | null = null;
            if (blueprintManagerOrError.__typename === 'PythonError') {
              message = blueprintManagerOrError.message;
            }

            return (
              <Alert
                intent="warning"
                title={
                  <Group direction="row" spacing={4}>
                    <div>Could not load blueprintmanager.</div>
                    {message && (
                      <ButtonLink
                        color={Colors.linkDefault()}
                        underline="always"
                        onClick={() => {
                          showCustomAlert({
                            title: 'Python error',
                            body: message,
                          });
                        }}
                      >
                        View error
                      </ButtonLink>
                    )}
                  </Group>
                }
              />
            );
          }

          return (
            <div style={{height: '100%', display: 'flex'}}>
              <SplitPanelContainer
                identifier="blueprint-manager-details"
                firstInitialPercent={50}
                firstMinSize={400}
                first={
                  <Box>
                    <Box
                      flex={{
                        direction: 'row',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                      padding={{vertical: 12, horizontal: 16}}
                    >
                      <Subheading>{blueprintManager?.blueprints.length} Blueprints</Subheading>
                      <Button
                        intent="primary"
                        icon={<Icon name="add" />}
                        onClick={() => openEditorForNewBlueprint()}
                      >
                        Create new Blueprint
                      </Button>
                    </Box>
                    <Table>
                      <thead>
                        <tr>
                          <th>Blueprint Name</th>
                        </tr>
                      </thead>
                      <tbody>
                        {blueprintManager?.blueprints.map((blueprint) => {
                          return (
                            <tr key={blueprint.id}>
                              <td>
                                <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                                  <Box
                                    flex={{direction: 'row', alignItems: 'center', gap: 4}}
                                    style={{maxWidth: '100%'}}
                                  >
                                    <Icon name="add_circle" color={Colors.accentBlue()} />
                                    <div
                                      style={{
                                        maxWidth: '100%',
                                        whiteSpace: 'nowrap',
                                        fontWeight: 500,
                                      }}
                                    >
                                      {blueprint.key.identifierWithinManager}
                                    </div>
                                  </Box>
                                  <Button
                                    icon={<Icon name="edit" />}
                                    onClick={() => openEditorForBlueprint(blueprint)}
                                  />
                                </Box>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </Table>
                    <EditBlueprintDialog
                      isOpen={isEditorOpen}
                      onClose={() => setIsEditorOpen(false)}
                      configSchema={jsonSchemaConfigSchema}
                      config={config}
                      setConfig={setConfig}
                      loading={createLoading.loading || updateLoading.loading}
                      createdPRUrl={createdPRUrl}
                      title={
                        editorTarget
                          ? `Edit Blueprint ${editorTarget?.identifierWithinManager}`
                          : 'Create new Blueprint'
                      }
                      name={editorTarget?.identifierWithinManager.split('.')[0] || inputName}
                      setName={setInputName}
                      canSetName={!editorTarget}
                      onSave={saveConfig}
                    />
                  </Box>
                }
                second={
                  <Box padding={{bottom: 48}} style={{overflowY: 'auto'}}>
                    <Box
                      flex={{gap: 4, direction: 'column'}}
                      margin={{left: 24, right: 12, vertical: 16}}
                    >
                      <Heading>{blueprintManager?.name}</Heading>
                    </Box>
                    <Box
                      border="top-and-bottom"
                      background={Colors.backgroundLight()}
                      padding={{vertical: 8, horizontal: 24}}
                      style={{fontSize: '12px', fontWeight: 500}}
                    >
                      Description
                    </Box>
                    <Box padding={{horizontal: 24, vertical: 16}}>
                      {blueprintManager?.name === 'ingestion' ? (
                        <>
                          Blueprints for ELT syncs using Sling.
                          <br /> <br />
                          To create a blueprint, hit the new blueprint button and be prepared to
                          supply Sling stream config.
                          <br /> <br />
                          https://docs.slingdata.io/sling-cli/run/configuration/replication
                        </>
                      ) : (
                        <>Blueprints for Python notebooks for model training.</>
                      )}
                    </Box>
                  </Box>
                }
              />
            </div>
          );
        }}
      </Loading>
    </Page>
  );
};

const BLUEPRINT_MANAGER_ROOT_QUERY = gql`
  query BlueprintManagerRootQuery($blueprintManagerSelector: BlueprintManagerSelector!) {
    blueprintManagerOrError(blueprintManagerSelector: $blueprintManagerSelector) {
      __typename
      ... on BlueprintManager {
        id
        name
        schema {
          schema
        }
        blueprints {
          id
          key {
            managerName
            identifierWithinManager
          }
          blob {
            value
          }
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

const CREATE_BLUEPRINT_MUTATION = gql`
  mutation CreateBlueprintMutation(
    $blueprintManagerSelector: BlueprintManagerSelector!
    $blob: String!
    $identifierWithinManager: String!
  ) {
    createBlueprint(
      blueprintManagerSelector: $blueprintManagerSelector
      blob: $blob
      identifierWithinManager: $identifierWithinManager
    )
  }
`;

const UPDATE_BLUEPRINT_MUTATION = gql`
  mutation UpdateBlueprintMutation(
    $blueprintManagerSelector: BlueprintManagerSelector!
    $blob: String!
    $identifierWithinManager: String!
  ) {
    updateBlueprint(
      blueprintManagerSelector: $blueprintManagerSelector
      blob: $blob
      identifierWithinManager: $identifierWithinManager
    )
  }
`;

const FormLabel = styled.label`
  font-size: 12px;
`;
