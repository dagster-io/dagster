import * as React from 'react';
import styled from 'styled-components/macro';

import {Colors} from './Colors';
import {Popover} from './Popover';
import {ConfigSchema_allConfigTypes as TypeData} from './configeditor/types/ConfigSchema';
import {FontFamily} from './styles';

type ConfigTypeSchemaTheme = 'dark' | 'light';

export type {TypeData};

interface ConfigTypeSchemaProps {
  type: TypeData;
  typesInScope: TypeData[];
  theme?: ConfigTypeSchemaTheme;
  maxDepth?: number;
}

function renderTypeRecursive(
  type: TypeData,
  typeLookup: {[typeName: string]: TypeData},
  depth: number,
  props: ConfigTypeSchemaProps,
): React.ReactElement<HTMLElement> {
  if (type.__typename === 'CompositeConfigType' && props.maxDepth && depth === props.maxDepth) {
    return <span>...</span>;
  }

  if (type.__typename === 'CompositeConfigType') {
    const innerIndent = '  '.repeat(depth + 1);
    return (
      <>
        {`{`}
        {type.isSelector && (
          <DictBlockComment indent={innerIndent} content="One of the following:" />
        )}
        {type.fields.map((fieldData) => {
          const keyDisplay = (
            <DictKey
              theme={props.theme}
              style={
                fieldData.defaultValueAsJson
                  ? {borderBottom: `dashed ${Colors.Blue200} 1px`, cursor: 'pointer'}
                  : undefined
              }
            >
              {fieldData.name}
            </DictKey>
          );
          return (
            <DictEntry key={fieldData.name}>
              <DictBlockComment indent={innerIndent} content={fieldData.description} />
              {innerIndent}
              {fieldData.defaultValueAsJson ? (
                <Popover
                  popoverClassName="config-tooltip"
                  interactionKind="hover"
                  hoverCloseDelay={100}
                  content={<ConfigContent value={fieldData.defaultValueAsJson} />}
                >
                  {keyDisplay}
                </Popover>
              ) : (
                keyDisplay
              )}
              {!fieldData.isRequired && Optional}
              {`: `}
              {renderTypeRecursive(
                typeLookup[fieldData.configTypeKey]!,
                typeLookup,
                depth + 1,
                props,
              )}
            </DictEntry>
          );
        })}
        {'  '.repeat(depth) + '}'}
      </>
    );
  }

  if (type.__typename === 'ArrayConfigType') {
    const ofTypeKey = type.typeParamKeys[0]!;
    return <>[{renderTypeRecursive(typeLookup[ofTypeKey]!, typeLookup, depth, props)}]</>;
  }

  if (type.__typename === 'MapConfigType') {
    // e.g.
    // {
    //   [name_hint: String]: Int
    // }
    const keyTypeKey = type.typeParamKeys[0]!;
    const valueTypeKey = type.typeParamKeys[1]!;
    const innerIndent = '  '.repeat(depth + 1);
    return (
      <>
        {`{`}
        <DictEntry>
          {innerIndent}[{type.keyLabelName ? `${type.keyLabelName}: ` : null}
          {renderTypeRecursive(typeLookup[keyTypeKey]!, typeLookup, depth + 1, props)}]{`: `}
          {renderTypeRecursive(typeLookup[valueTypeKey]!, typeLookup, depth + 1, props)}
        </DictEntry>
        {'  '.repeat(depth) + '}'}
      </>
    );
  }

  if (type.__typename === 'NullableConfigType') {
    const ofTypeKey = type.typeParamKeys[0]!;
    return (
      <>
        {renderTypeRecursive(typeLookup[ofTypeKey]!, typeLookup, depth, props)}
        {Optional}
      </>
    );
  }

  if (type.__typename === 'ScalarUnionConfigType') {
    const nonScalarTypeMarkup = renderTypeRecursive(
      typeLookup[type.nonScalarTypeKey]!,
      typeLookup,
      depth,
      props,
    );
    const scalarTypeMarkup = renderTypeRecursive(
      typeLookup[type.scalarTypeKey]!,
      typeLookup,
      depth,
      props,
    );

    return (
      <span>
        {scalarTypeMarkup} | {nonScalarTypeMarkup}
      </span>
    );
  }

  return <span>{type.givenName}</span>;
}

const prettyJsonString = (value: string) => {
  try {
    const parsed = JSON.parse(value);
    return JSON.stringify(parsed, null, 2);
  } catch (e) {
    return value;
  }
};

const ConfigContent = React.memo(({value}: {value: string}) => (
  <>
    <ConfigHeader>
      <strong>Default value</strong>
    </ConfigHeader>
    <ConfigJSON>{prettyJsonString(value)}</ConfigJSON>
  </>
));

const ConfigHeader = styled.div`
  background-color: ${Colors.Gray800};
  color: ${Colors.White};
  font-size: 13px;
  padding: 8px;
`;

const ConfigJSON = styled.pre`
  background-color: ${Colors.Gray900};
  color: ${Colors.White};
  whitespace: pre-wrap;
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  padding: 8px;
  margin: 0;
`;

export const ConfigTypeSchema = React.memo((props: ConfigTypeSchemaProps) => {
  const {type, typesInScope} = props;

  const typeLookup: Record<string, TypeData> = {};
  for (const typeInScope of typesInScope) {
    typeLookup[typeInScope.key] = typeInScope;
  }

  return (
    <TypeSchemaContainer>
      <DictBlockComment content={type.description} indent="" />
      {renderTypeRecursive(type, typeLookup, 0, props)}
    </TypeSchemaContainer>
  );
});

const TypeSchemaContainer = styled.code`
  color: ${Colors.Gray400};
  display: block;
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 18px;
`;

const DictEntry = styled.div``;

const DictKey = styled.span<{theme: ConfigTypeSchemaTheme | undefined}>`
  color: ${({theme}) => (theme === 'dark' ? Colors.White : Colors.Dark)};
`;

const DictComment = styled.div`
  /* This allows long comments to wrap as nice indented blocks, while
     copy/pasting as a single line with space-based indentation. */
  text-indent: -1.85em;
  padding-left: 1.85em;
  white-space: initial;
`;

const DictBlockComment = ({indent = '', content}: {indent: string; content: string | null}) =>
  content !== null && content !== '' ? (
    <DictComment>{`${indent.replace(/ /g, '\u00A0')}/* ${content} */`}</DictComment>
  ) : null;

const Optional = <span style={{fontWeight: 500, color: Colors.Yellow700}}>?</span>;
