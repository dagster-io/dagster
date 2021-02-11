import {gql} from '@apollo/client';
import {Button, Checkbox, Code, Colors, Icon, Intent, Position, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showCustomAlert} from 'src/app/CustomAlertProvider';
import {useConfirmation} from 'src/app/CustomConfirmationProvider';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {errorStackToYamlPath} from 'src/configeditor/ConfigEditorUtils';
import {
  ConfigEditorRunConfigSchemaFragment,
  ConfigEditorRunConfigSchemaFragment_allConfigTypes_CompositeConfigType,
} from 'src/configeditor/types/ConfigEditorRunConfigSchemaFragment';
import {
  RunPreviewValidationFragment,
  RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors,
} from 'src/execute/types/RunPreviewValidationFragment';
import {ButtonLink} from 'src/ui/ButtonLink';
import {SplitPanelContainer} from 'src/ui/SplitPanelContainer';

type ValidationError = RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors;
type ValidationErrorOrNode = ValidationError | React.ReactNode;

function isValidationError(e: ValidationErrorOrNode): e is ValidationError {
  return e && typeof e === 'object' && '__typename' in e ? true : false;
}

const stateToHint = {
  invalid: {
    title: `You need to fix this configuration section.`,
    intent: Intent.DANGER,
  },
  missing: {
    title: `You need to add this configuration section.`,
    intent: Intent.DANGER,
  },
  present: {
    title: `This section is present and valid.`,
    intent: Intent.SUCCESS,
  },
  none: {title: `This section is empty and valid.`, intent: Intent.PRIMARY},
};

const RemoveExtraConfigButton = ({
  onRemoveExtraPaths,
  extraNodes,
}: {
  extraNodes: string[];
  onRemoveExtraPaths: (paths: string[]) => void;
}) => {
  const confirm = useConfirmation();

  const knownKeyExtraPaths: {[key: string]: string[]} = {};
  const otherPaths: string[] = [];

  for (const path of extraNodes) {
    const parts = path.split('.');

    // If the length is 2, the first part of the path is a known key, such as "solids", "resouces",
    // or "loggers", and the user has provided extra config for one of those. We will keep track of
    // these in `knownKeyExtraPaths` just so we can display them with an extra description.
    if (parts.length === 2) {
      const [type, name] = parts;
      if (!knownKeyExtraPaths[type]) {
        knownKeyExtraPaths[type] = [];
      }
      knownKeyExtraPaths[type].push(name);
    } else {
      otherPaths.push(path);
    }
  }

  return (
    <div style={{marginTop: 5}}>
      <Button
        small={true}
        onClick={async () => {
          await confirm({
            title: 'Remove extra config',
            description: (
              <div>
                <p>
                  You have provided extra configuration in your run config which does not conform to
                  your pipeline{`'`}s config schema.
                </p>
                {Object.entries(knownKeyExtraPaths).length > 0 &&
                  Object.entries(knownKeyExtraPaths).map(([key, value]) => (
                    <>
                      <p>Extra {key}:</p>
                      <ul>
                        {value.map((v) => (
                          <li key={v}>
                            <Code>{v}</Code>
                          </li>
                        ))}
                      </ul>
                    </>
                  ))}
                {otherPaths.length > 0 && (
                  <>
                    <p>Other extra paths:</p>
                    <ul>
                      {otherPaths.map((v) => (
                        <li key={v}>
                          <Code>{v}</Code>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
                <p>
                  Clicking confirm will automatically remove this extra configuration from your run
                  config.
                </p>{' '}
              </div>
            ),
          });
          onRemoveExtraPaths(extraNodes);
        }}
      >
        Remove Extra Config
      </Button>
    </div>
  );
};

const ScaffoldConfigButton = ({
  onScaffoldMissingConfig,
  missingNodes,
}: {
  missingNodes: string[];
  onScaffoldMissingConfig: () => void;
}) => {
  const confirm = useConfirmation();

  const confirmationMessage = (
    <div>
      {missingNodes.length > 0 && (
        <>
          <p>Missing paths:</p>
          <ul>
            {missingNodes.map((v) => (
              <li key={v}>
                <Code>{v}</Code>
              </li>
            ))}
          </ul>
        </>
      )}
      <p>
        Clicking confirm will automatically scaffold this missing configuration into your run config
        with default values. You will need to change the values appropriately.
      </p>
    </div>
  );

  const onClick = async () => {
    await confirm({
      title: 'Scaffold extra config',
      description: confirmationMessage,
    });
    onScaffoldMissingConfig();
  };

  return (
    <div style={{marginTop: 5}}>
      <Button small={true} onClick={onClick}>
        Scaffold Missing Config
      </Button>
    </div>
  );
};

interface RunPreviewProps {
  validation: RunPreviewValidationFragment | null;
  document: any | null;

  actions?: React.ReactChild;
  runConfigSchema?: ConfigEditorRunConfigSchemaFragment;
  onHighlightPath: (path: string[]) => void;
  onRemoveExtraPaths: (paths: string[]) => void;
  onScaffoldMissingConfig: () => void;
  solidSelection: string[] | null;
}

interface RunPreviewState {
  errorsOnly: boolean;
}

export class RunPreview extends React.Component<RunPreviewProps, RunPreviewState> {
  state: RunPreviewState = {
    errorsOnly: false,
  };

  shouldComponentUpdate(nextProps: RunPreviewProps, nextState: RunPreviewState) {
    return (
      nextProps.validation !== this.props.validation ||
      nextProps.runConfigSchema !== this.props.runConfigSchema ||
      nextState.errorsOnly !== this.state.errorsOnly
    );
  }

  getRootCompositeChildren = () => {
    if (!this.props.runConfigSchema) {
      return {};
    }

    const {allConfigTypes, rootConfigType} = this.props.runConfigSchema;
    const children: {
      [fieldName: string]: ConfigEditorRunConfigSchemaFragment_allConfigTypes_CompositeConfigType;
    } = {};

    const root = allConfigTypes.find((t) => t.key === rootConfigType.key);
    if (root?.__typename !== 'CompositeConfigType') {
      return children;
    }

    root.fields.forEach((field) => {
      const allConfigVersion = allConfigTypes.find((t) => t.key === field.configTypeKey);
      if (allConfigVersion?.__typename !== 'CompositeConfigType') {
        return;
      }
      children[field.name] = allConfigVersion;
    });

    return children;
  };

  render() {
    const {
      actions,
      document,
      validation,
      onHighlightPath,
      onRemoveExtraPaths,
      onScaffoldMissingConfig,
      solidSelection,
    } = this.props;
    const {errorsOnly} = this.state;

    const extraNodes: string[] = [];
    const missingNodes: string[] = [];
    const errorsAndPaths: {
      pathKey: string;
      error: ValidationErrorOrNode;
    }[] = [];

    if (validation && validation.__typename === 'PipelineConfigValidationInvalid') {
      validation.errors.forEach((e) => {
        const path = errorStackToYamlPath(e.stack.entries);

        errorsAndPaths.push({pathKey: path.join('.'), error: e});

        if (e.__typename === 'MissingFieldConfigError') {
          missingNodes.push([...path, e.field.name].join('.'));
        } else if (e.__typename === 'MissingFieldsConfigError') {
          for (const field of e.fields) {
            missingNodes.push([...path, field.name].join('.'));
          }
        } else if (e.__typename === 'FieldNotDefinedConfigError') {
          extraNodes.push([...path, e.fieldName].join('.'));
        } else if (e.__typename === 'FieldsNotDefinedConfigError') {
          for (const fieldName of e.fieldNames) {
            extraNodes.push([...path, fieldName].join('.'));
          }
        } else if (e.__typename === 'RuntimeMismatchConfigError') {
          // If an entry at a path is the wrong type,
          // it is equivalent to it being missing
          missingNodes.push(path.join('.'));
        }
      });
    }

    if (validation?.__typename === 'InvalidSubsetError') {
      errorsAndPaths.push({pathKey: '', error: validation.message});
    }

    if (validation?.__typename === 'PythonError') {
      const info = <PythonErrorInfo error={validation} />;
      errorsAndPaths.push({
        pathKey: '',
        error: (
          <span>
            PythonError:{' '}
            <ButtonLink onClick={() => showCustomAlert({body: info})}>Click for details</ButtonLink>
          </span>
        ),
      });
    }

    const {resources, solids, ...rest} = this.getRootCompositeChildren();

    const itemsIn = (parents: string[], items: {name: string; isRequired: boolean}[]) => {
      const boxes = items
        .map((item) => {
          // If a solid selection is in use, discard anything not in it.
          if (solidSelection?.length && !solidSelection?.includes(item.name)) {
            return null;
          }

          const path = [...parents, item.name];
          const pathKey = path.join('.');
          const pathErrors = errorsAndPaths
            .filter((e) => e.pathKey === pathKey || e.pathKey.startsWith(`${pathKey}.`))
            .map((e) => e.error);

          const isPresent = pathExistsInObject(path, document);
          const containsMissing = missingNodes.some((missingNode) =>
            missingNode.includes(path.join('.')),
          );
          const isInvalid = pathErrors.length || containsMissing;
          const isMissing = path.some((_, idx) =>
            missingNodes.includes(path.slice(0, idx + 1).join('.')),
          );
          if (errorsOnly && !isInvalid) {
            return false;
          }
          const state =
            isMissing && item.isRequired
              ? 'missing'
              : isInvalid
              ? 'invalid'
              : isPresent
              ? 'present'
              : 'none';

          return (
            <Tooltip
              position={Position.BOTTOM}
              content={stateToHint[state].title}
              intent={stateToHint[state].intent}
              key={item.name}
            >
              <Item
                key={item.name}
                state={state}
                onClick={() => {
                  const first = pathErrors.find(isValidationError);
                  onHighlightPath(first ? errorStackToYamlPath(first.stack.entries) : path);
                }}
              >
                {item.name}
              </Item>
            </Tooltip>
          );
        })
        .filter(Boolean);

      if (!boxes.length) {
        return <ItemsEmptyNotice>Nothing to display.</ItemsEmptyNotice>;
      }
      return boxes;
    };

    return (
      <SplitPanelContainer
        identifier="run-preview"
        axis="horizontal"
        first={
          <ErrorListContainer>
            <Section>
              <SectionTitle>Errors</SectionTitle>
              {errorsAndPaths.map((item, idx) => (
                <ErrorRow key={idx} error={item.error} onHighlight={onHighlightPath} />
              ))}
            </Section>

            {(extraNodes.length > 0 || missingNodes.length > 0) && (
              <Section>
                <SectionTitle>Bulk Actions:</SectionTitle>
                {extraNodes.length ? (
                  <RemoveExtraConfigButton
                    onRemoveExtraPaths={onRemoveExtraPaths}
                    extraNodes={extraNodes}
                  />
                ) : null}
                {missingNodes.length ? (
                  <ScaffoldConfigButton
                    onScaffoldMissingConfig={onScaffoldMissingConfig}
                    missingNodes={missingNodes}
                  />
                ) : null}
              </Section>
            )}
          </ErrorListContainer>
        }
        firstInitialPercent={50}
        firstMinSize={150}
        second={
          <>
            <div style={{overflowY: 'scroll', width: '100%', height: '100%'}}>
              <RuntimeAndResourcesSection>
                <Section>
                  <SectionTitle>Runtime</SectionTitle>
                  <ItemSet>
                    {itemsIn(
                      [],
                      Object.keys(rest).map((name) => ({name, isRequired: false})),
                    )}
                  </ItemSet>
                </Section>
                {(resources?.fields.length || 0) > 0 && (
                  <Section>
                    <SectionTitle>Resources</SectionTitle>
                    <ItemSet>{itemsIn(['resources'], resources?.fields || [])}</ItemSet>
                  </Section>
                )}
              </RuntimeAndResourcesSection>
              <Section>
                <SectionTitle>Solids</SectionTitle>
                <ItemSet>{itemsIn(['solids'], solids?.fields || [])}</ItemSet>
              </Section>
              <div style={{height: 50}} />
            </div>
            <div
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                padding: '12px 15px 0px 10px',
                background: 'rgba(255,255,255,0.7)',
              }}
            >
              <Checkbox
                label="Errors Only"
                checked={errorsOnly}
                onChange={() => this.setState({errorsOnly: !errorsOnly})}
              />
            </div>
            <div style={{position: 'absolute', bottom: 14, right: 14}}>{actions}</div>
          </>
        }
      />
    );
  }
}

export const RUN_PREVIEW_VALIDATION_FRAGMENT = gql`
  fragment RunPreviewValidationFragment on PipelineConfigValidationResult {
    __typename
    ... on PipelineConfigValidationInvalid {
      errors {
        __typename
        reason
        message
        stack {
          entries {
            __typename
            ... on EvaluationStackPathEntry {
              fieldName
            }
            ... on EvaluationStackListItemEntry {
              listIndex
            }
          }
        }
        ... on MissingFieldConfigError {
          field {
            name
          }
        }
        ... on MissingFieldsConfigError {
          fields {
            name
          }
        }
        ... on FieldNotDefinedConfigError {
          fieldName
        }
        ... on FieldsNotDefinedConfigError {
          fieldNames
        }
      }
    }
    ... on PipelineNotFoundError {
      message
    }
    ... on InvalidSubsetError {
      message
    }
    ...PythonErrorFragment
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

const SectionTitle = styled.div`
  color: ${Colors.GRAY3};
  text-transform: uppercase;
  font-size: 12px;
`;

const Section = styled.div`
  margin-top: 14px;
  margin-left: 10px;
`;

const ItemSet = styled.div`
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
`;

const ItemsEmptyNotice = styled.div`
  font-size: 13px;
  padding-top: 7px;
  padding-bottom: 7px;
`;

const ItemBorder = {
  invalid: `1px solid #CE1126`,
  missing: `1px solid #CE1126`,
  present: `1px solid #AFCCE1`,
  none: `1px solid ${Colors.LIGHT_GRAY2}`,
};

const ItemBackground = {
  invalid: Colors.RED5,
  missing: Colors.RED5,
  present: '#C8E1F4',
  none: Colors.LIGHT_GRAY4,
};

const ItemBackgroundHover = {
  invalid: '#E15858',
  missing: '#E15858',
  present: '#AFCCE1',
  none: Colors.LIGHT_GRAY4,
};

const ItemColor = {
  invalid: Colors.WHITE,
  missing: Colors.WHITE,
  present: Colors.BLACK,
  none: Colors.BLACK,
};

const Item = styled.div<{
  state: 'present' | 'missing' | 'invalid' | 'none';
}>`
  white-space: nowrap;
  font-size: 13px;
  color: ${({state}) => ItemColor[state]};
  background: ${({state}) => ItemBackground[state]};
  border-radius: 3px;
  border: ${({state}) => ItemBorder[state]};
  padding: 3px 5px;
  margin: 3px;
  transition: background 150ms linear, color 150ms linear;
  cursor: ${({state}) => (state === 'present' ? 'default' : 'not-allowed')};
  overflow: hidden;
  text-overflow: ellipsis;

  &:hover {
    transition: none;
    background: ${({state}) => ItemBackgroundHover[state]};
  }
`;

const ErrorListContainer = styled.div`
  margin-left: 10px;
  overflow-y: scroll;
  height: 100%;
`;

const ErrorRowContainer = styled.div<{hoverable: boolean}>`
  text-align: left;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  border-bottom: 1px solid #ccc;
  padding: 7px 0;
  padding-right: 7px;
  margin-bottom: 8px;
  &:last-child {
    border-bottom: 0;
    margin-bottom: 15px;
  }
  ${({hoverable}) =>
    hoverable &&
    `&:hover {
      background: ${Colors.LIGHT_GRAY5};
    }
  `}
`;

const RuntimeAndResourcesSection = styled.div`
  display: flex;
  @media (max-width: 800px) {
    flex-direction: column;
  }
`;

const ErrorRow: React.FunctionComponent<{
  error: ValidationError | React.ReactNode;
  onHighlight: (path: string[]) => void;
}> = ({error, onHighlight}) => {
  let message = error;
  let target: ValidationError | null = null;
  if (isValidationError(error)) {
    message = error.message;
    target = error;
  }

  let displayed = message;
  if (typeof message === 'string' && message.length > 400) {
    displayed = truncateErrorMessage(message);
  }

  return (
    <ErrorRowContainer
      hoverable={!!target}
      onClick={() => target && onHighlight(errorStackToYamlPath(target.stack.entries))}
    >
      <div style={{paddingRight: 8}}>
        <Icon icon="error" iconSize={14} color={Colors.RED4} />
      </div>
      <div>
        {displayed}
        {displayed !== message && (
          <>
            &nbsp;
            <ButtonLink
              onClick={() =>
                showCustomAlert({
                  body: <div style={{whiteSpace: 'pre-wrap'}}>{message}</div>,
                })
              }
            >
              View all
            </ButtonLink>
          </>
        )}
      </div>
    </ErrorRowContainer>
  );
};

function truncateErrorMessage(message: string) {
  let split = message.indexOf('{');
  if (split === -1) {
    split = message.indexOf('. ');
  }
  if (split === -1) {
    split = 400;
  }
  return message.substr(0, split) + '... ';
}

function pathExistsInObject(path: string[], object: any): boolean {
  if (!object || typeof object !== 'object') {
    return false;
  }
  if (path.length === 0) {
    return true;
  }
  const [first, ...rest] = path;
  return pathExistsInObject(rest, object[first]);
}
