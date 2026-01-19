import {
  Box,
  Button,
  ButtonLink,
  Checkbox,
  Code,
  Colors,
  FontFamily,
  Icon,
  Intent,
  SplitPanelContainer,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {LaunchpadType} from './types';
import {gql} from '../apollo-client';
import {
  RunPreviewValidationErrorsFragment,
  RunPreviewValidationFragment,
} from './types/RunPreview.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {useConfirmation} from '../app/CustomConfirmationProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {errorStackToYamlPath} from '../configeditor/ConfigEditorUtils';
import {
  CompositeConfigTypeForSchemaFragment,
  ConfigEditorRunConfigSchemaFragment,
} from '../configeditor/types/ConfigEditorUtils.types';

type ValidationError = RunPreviewValidationErrorsFragment;
type ValidationErrorOrNode = ValidationError | React.ReactNode;

function isValidationError(e: ValidationErrorOrNode): e is ValidationError {
  return e && typeof e === 'object' && '__typename' in e ? true : false;
}

type State = 'invalid' | 'missing' | 'present' | 'none';

const stateToHint: Record<State, {title: string; intent: Intent}> = {
  invalid: {
    title: `此配置节需要修复。`,
    intent: 'danger',
  },
  missing: {
    title: `需要添加此配置节。`,
    intent: 'danger',
  },
  present: {
    title: `此配置节存在且有效。`,
    intent: 'none',
  },
  none: {title: `此配置节为空但有效。`, intent: 'none'},
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

    // If the length is 2, the first part of the path is a known key, such as "solids", "resources",
    // or "loggers", and the user has provided extra config for one of those. We will keep track of
    // these in `knownKeyExtraPaths` just so we can display them with an extra description.
    if (parts.length === 2) {
      const [type, name] = parts;
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const target = knownKeyExtraPaths[type!] || [];
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      target.push(name!);
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      knownKeyExtraPaths[type!] = target;
    } else {
      otherPaths.push(path);
    }
  }

  const onClick = async () => {
    await confirm({
      title: '移除多余配置',
      description: (
        <div>
          <p>
            {`您的运行配置中包含不符合流水线配置模式的多余配置。`}
          </p>
          {Object.entries(knownKeyExtraPaths).length > 0 &&
            Object.entries(knownKeyExtraPaths).map(([key, value]) => (
              <React.Fragment key={key}>
                <p>多余的 {key}:</p>
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
              <p>其他多余路径:</p>
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
            点击确认将自动从运行配置中移除这些多余配置。
          </p>
        </div>
      ),
    });
    onRemoveExtraPaths(extraNodes);
  };

  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <Button disabled={disabled} onClick={onClick}>
        移除多余配置
      </Button>
      {disabled ? (
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <Icon name="check_circle" color={Colors.accentGreen()} />
          无多余配置需要移除
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
          <p>缺失的路径:</p>
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
        点击确认将使用默认值自动填充缺失的配置到您的运行配置中。您需要根据需要修改这些值。
      </p>
    </div>
  );

  const onClick = async () => {
    await confirm({
      title: '填充缺失配置',
      description: confirmationMessage,
    });
    onScaffoldMissingConfig();
  };

  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <Button disabled={disabled} onClick={onClick}>
        填充缺失配置
      </Button>
      {disabled ? (
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <Icon name="check_circle" color={Colors.accentGreen()} />
          无缺失配置
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
      title: '填充所有默认配置',
      description: (
        <div>
          点击确认将使用默认值自动填充所有未指定的配置字段到您的运行配置中。您需要根据需要修改这些值。
        </div>
      ),
    });
    onExpandDefaults();
  };

  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <Button disabled={disabled} onClick={onClick}>
        填充所有默认配置
      </Button>
      {disabled ? (
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <Icon name="check_circle" color={Colors.accentGreen()} />
          所有默认值已填充
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
          Python错误:{' '}
          <ButtonLink onClick={() => showCustomAlert({body: info})}>点击查看详情</ButtonLink>
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

        const hint = stateToHint[state];
        return (
          <Tooltip position="bottom" content={hint.title} key={item.name}>
            <Tag key={item.name} intent={hint.intent}>
              <ButtonLink
                onClick={() => {
                  const first = pathErrors.find(isValidationError);
                  onHighlightPath(first ? errorStackToYamlPath(first.stack.entries) : path);
                }}
              >
                {item.name}
              </ButtonLink>
            </Tag>
          </Tooltip>
        );
      })
      .filter(Boolean);

    if (!boxes.length) {
      return <ItemsEmptyNotice>无内容显示。</ItemsEmptyNotice>;
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
            <SectionTitle>错误</SectionTitle>
            {errorsAndPaths.length ? (
              errorsAndPaths.map((item, idx) => (
                <ErrorRow key={idx} error={item.error} onHighlight={onHighlightPath} />
              ))
            ) : (
              <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                <Icon name="check_circle" color={Colors.accentGreen()} />
                无错误
              </Box>
            )}
          </Section>
          <Section>
            <SectionTitle>配置操作:</SectionTitle>
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
                <SectionTitle>运行时</SectionTitle>
                <ItemSet>
                  {itemsIn(
                    [],
                    Object.keys(rest).map((name) => ({name, isRequired: false})),
                  )}
                </ItemSet>
              </Section>
              {(resources?.fields.length || 0) > 0 && (
                <Section>
                  <SectionTitle>资源</SectionTitle>
                  <ItemSet>{itemsIn(['resources'], resources?.fields || [])}</ItemSet>
                </Section>
              )}
            </RuntimeAndResourcesSection>
            <Section>
              <SectionTitle>{launchpadType === 'asset' ? '资产 (算子)' : '算子'}</SectionTitle>
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
              background: Colors.backgroundDefault(),
            }}
          >
            <Checkbox
              label="仅显示错误"
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
  color: ${Colors.textLight()};
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
  font-size: 11px;
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
      background: ${Colors.backgroundLight()};
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
        <Icon name="error" color={Colors.accentRed()} />
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
              查看全部
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
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  return pathExistsInObject(rest, object[first!]);
}
