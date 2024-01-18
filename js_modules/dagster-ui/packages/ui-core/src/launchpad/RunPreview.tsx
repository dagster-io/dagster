import * as React from 'react';
import {gql} from '@apollo/client';
// eslint-disable-next-line no-restricted-imports
import {Intent} from '@blueprintjs/core';
import styled from 'styled-components';

import {
  Box,
  Button,
  ButtonLink,
  Checkbox,
  Code,
  FontFamily,
  Icon,
  SplitPanelContainer,
  Tag,
  Tooltip,
  colorAccentGreen,
  colorAccentRed,
  colorBackgroundDefault,
  colorBackgroundLight,
  colorTextLight,
} from '@dagster-io/ui-components';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {useConfirmation} from '../app/CustomConfirmationProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {errorStackToYamlPath} from '../configeditor/ConfigEditorUtils';
import {
  CompositeConfigTypeForSchemaFragment,
  ConfigEditorRunConfigSchemaFragment,
} from '../configeditor/types/ConfigEditorUtils.types';
import {LaunchpadType} from './types';
import {
  RunPreviewValidationErrorsFragment,
  RunPreviewValidationFragment,
} from './types/RunPreview.types';

type ValidationError = RunPreviewValidationErrorsFragment;
type ValidationErrorOrNode = ValidationError | React.ReactNode;

function isValidationError(e: ValidationErrorOrNode): e is ValidationError {
  return e && typeof e === 'object' && '__typename' in e ? true : false;
}

const stateToHint: {[key: string]: {title: string; intent: Intent}} = {
  invalid: {
    title: `You need to fix this configuration section.`,
    intent: 'danger',
  },
  missing: {
    title: `You need to add this configuration section.`,
    intent: 'danger',
  },
  present: {
    title: `This section is present and valid.`,
    intent: 'none',
  },
  none: {title: `This section is empty and valid.`, intent: 'none'},
};

const RemoveExtraConfigButton = ({
  onRemoveExtraPaths,
  extraNodes,
  disabled,
}: {
  extraNodes: string[];
  onRemoveExtraPaths: (paths: string[]) => void;
  disabled: boolean;
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
      const target = knownKeyExtraPaths[type!] || [];
      target.push(name!);
      knownKeyExtraPaths[type!] = target;
    } else {
      otherPaths.push(path);
    }
  }

  const onClick = async () => {
    await confirm({
      title: 'Remove extra config',
      description: (
        <div>
          <p>
            {`You have provided extra configuration in your run config which does not conform to your
            pipeline's config schema.`}
          </p>
          {Object.entries(knownKeyExtraPaths).length > 0 &&
            Object.entries(knownKeyExtraPaths).map(([key, value]) => (
              <React.Fragment key={key}>
                <p>Extra {key}:</p>
                <ul>
                  {value.map((v) => (
                    <li key={v}>
                      <Code>{v}</Code>
                    </li>
                  ))}
                </ul>
              </React.Fragment>
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
          </p>
        </div>
      ),
    });
    onRemoveExtraPaths(extraNodes);
  };

  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <Button disabled={disabled} onClick={onClick}>
        Remove extra config
      </Button>
      {disabled ? (
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <Icon name="check_circle" color={colorAccentGreen()} />
          No extra config to remove
        </Box>
      ) : null}
    </Box>
  );
};

const ScaffoldConfigButton = ({
  onScaffoldMissingConfig,
  missingNodes,
  disabled,
}: {
  missingNodes: string[];
  onScaffoldMissingConfig: () => void;
  disabled: boolean;
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
      title: 'Scaffold missing config',
      description: confirmationMessage,
    });
    onScaffoldMissingConfig();
  };

  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <Button disabled={disabled} onClick={onClick}>
        Scaffold missing config
      </Button>
      {disabled ? (
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <Icon name="check_circle" color={colorAccentGreen()} />
          No missing config
        </Box>
      ) : null}
    </Box>
  );
};

const ExpandDefaultButton = ({
  onExpandDefaults,
  disabled,
}: {
  onExpandDefaults: () => void;
  disabled: boolean;
}) => {
  const confirm = useConfirmation();

  const onClick = async () => {
    await confirm({
      title: 'Scaffold all default config',
      description: (
        <div>
          Clicking confirm will automatically scaffold any unspecified configuration fields into
          your run config with default values. You will need to change the values appropriately.
        </div>
      ),
    });
    onExpandDefaults();
  };

  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <Button disabled={disabled} onClick={onClick}>
        Scaffold all default config
      </Button>
      {disabled ? (
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <Icon name="check_circle" color={colorAccentGreen()} />
          All defaults expanded
        </Box>
      ) : null}
    </Box>
  );
};

interface RunPreviewProps {
  validation: RunPreviewValidationFragment | null;
  document: any | null;
  launchpadType: LaunchpadType;

  runConfigSchema?: ConfigEditorRunConfigSchemaFragment;
  onHighlightPath: (path: string[]) => void;
  onRemoveExtraPaths: (paths: string[]) => void;
  onScaffoldMissingConfig: () => void;
  onExpandDefaults: () => void;
  anyDefaultsToExpand: boolean;
  solidSelection: string[] | null;
}

export const RunPreview = (props: RunPreviewProps) => {
  const {
    document,
    validation,
    onHighlightPath,
    launchpadType,
    onRemoveExtraPaths,
    onScaffoldMissingConfig,
    onExpandDefaults,
    anyDefaultsToExpand,
    solidSelection,
    runConfigSchema,
  } = props;
  const [errorsOnly, setErrorsOnly] = React.useState(false);

  const rootCompositeChildren = React.useMemo(() => {
    if (!runConfigSchema) {
      return {};
    }

    const {allConfigTypes, rootConfigType} = runConfigSchema;
    const children: {
      [fieldName: string]: CompositeConfigTypeForSchemaFragment;
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
  }, [runConfigSchema]);

  const extraNodes: string[] = [];
  const missingNodes: string[] = [];
  const errorsAndPaths: {
    pathKey: string;
    error: ValidationErrorOrNode;
  }[] = [];

  if (validation && validation.__typename === 'RunConfigValidationInvalid') {
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

  const {resources, ops, solids, ...rest} = rootCompositeChildren;
  const hasOps = !!ops?.fields;

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
            position="bottom"
            content={stateToHint[state]!.title}
            intent={stateToHint[state]!.intent}
            key={item.name}
          >
            <Tag
              key={item.name}
              intent={stateToHint[state]!.intent}
              onClick={() => {
                const first = pathErrors.find(isValidationError);
                onHighlightPath(first ? errorStackToYamlPath(first.stack.entries) : path);
              }}
            >
              {item.name}
            </Tag>
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
            {errorsAndPaths.length ? (
              errorsAndPaths.map((item, idx) => (
                <ErrorRow key={idx} error={item.error} onHighlight={onHighlightPath} />
              ))
            ) : (
              <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                <Icon name="check_circle" color={colorAccentGreen()} />
                No errors
              </Box>
            )}
          </Section>
          <Section>
            <SectionTitle>Config actions:</SectionTitle>
            <Box flex={{direction: 'column', gap: 8}} padding={{top: 4, bottom: 20}}>
              <ScaffoldConfigButton
                onScaffoldMissingConfig={onScaffoldMissingConfig}
                missingNodes={missingNodes}
                disabled={!missingNodes.length}
              />
              <ExpandDefaultButton
                onExpandDefaults={onExpandDefaults}
                disabled={!anyDefaultsToExpand}
              />
              <RemoveExtraConfigButton
                onRemoveExtraPaths={onRemoveExtraPaths}
                extraNodes={extraNodes}
                disabled={!extraNodes.length}
              />
            </Box>
          </Section>
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
              <SectionTitle>{launchpadType === 'asset' ? 'Assets (Ops)' : 'Ops'}</SectionTitle>
              <ItemSet>
                {itemsIn(
                  [hasOps ? 'ops' : 'solids'],
                  (hasOps ? ops?.fields : solids?.fields) || [],
                )}
              </ItemSet>
            </Section>
            <div style={{height: 50}} />
          </div>
          <div
            style={{
              position: 'absolute',
              top: 0,
              right: 0,
              padding: '12px 15px 0px 10px',
              background: colorBackgroundDefault(),
            }}
          >
            <Checkbox
              label="Errors only"
              checked={errorsOnly}
              onChange={() => setErrorsOnly(!errorsOnly)}
            />
          </div>
        </>
      }
    />
  );
};

export const RUN_PREVIEW_VALIDATION_FRAGMENT = gql`
  fragment RunPreviewValidationFragment on PipelineConfigValidationResult {
    ... on RunConfigValidationInvalid {
      errors {
        ...RunPreviewValidationErrors
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

  fragment RunPreviewValidationErrors on PipelineConfigValidationError {
    reason
    message
    stack {
      entries {
        ... on EvaluationStackPathEntry {
          fieldName
        }
        ... on EvaluationStackListItemEntry {
          listIndex
        }
        ... on EvaluationStackMapKeyEntry {
          mapKey
        }
        ... on EvaluationStackMapValueEntry {
          mapKey
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

  ${PYTHON_ERROR_FRAGMENT}
`;

const SectionTitle = styled.div`
  color: ${colorTextLight()};
  text-transform: uppercase;
  font-size: 12px;
  margin-bottom: 8px;
`;

const Section = styled.div`
  margin-top: 14px;
  margin-left: 10px;
`;

const ItemSet = styled.div`
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 4px;
`;

const ItemsEmptyNotice = styled.div`
  font-size: 13px;
  padding-top: 7px;
  padding-bottom: 7px;
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
  font-family: ${FontFamily.monospace};
  cursor: pointer;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  border-bottom: 1px solid #ccc;
  padding: 8px;
  margin: 8px 12px 0 -8px;
  &:last-child {
    border-bottom: 0;
    margin-bottom: 15px;
  }
  ${({hoverable}) =>
    hoverable &&
    `&:hover {
      background: ${colorBackgroundLight()};
    }
  `}
`;

const RuntimeAndResourcesSection = styled.div`
  display: flex;
  gap: 12px;
  @media (max-width: 800px) {
    flex-direction: column;
  }
`;

const ErrorRow = ({
  error,
  onHighlight,
}: {
  error: ValidationError | React.ReactNode;
  onHighlight: (path: string[]) => void;
}) => {
  let message: React.ReactNode = null;
  let target: ValidationError | null = null;
  if (isValidationError(error)) {
    message = error.message;
    target = error;
  } else {
    message = error;
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
      <div style={{paddingRight: 4}}>
        <Icon name="error" color={colorAccentRed()} />
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
  return pathExistsInObject(rest, object[first!]);
}
