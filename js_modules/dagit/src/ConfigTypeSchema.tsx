import {Colors} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import styled from 'styled-components/macro';

type ConfigTypeSchemaTheme = 'dark' | 'light';

interface ConfigTypeSchemaProps {
  type: TypeData;
  typesInScope: TypeData[];
  theme?: ConfigTypeSchemaTheme;
  maxDepth?: number;
}

interface FieldData {
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

interface CommonTypeData {
  key: string;
  description: string | null;
}

interface CompositeTypeData extends CommonTypeData {
  __typename: 'CompositeConfigType';
  isSelector: boolean;
  fields: FieldData[];
}

interface ListTypeData extends CommonTypeData {
  __typename: 'ArrayConfigType';
  typeParamKeys: string[];
}

interface NullableTypeData extends CommonTypeData {
  __typename: 'NullableConfigType';
  typeParamKeys: string[];
}

interface EnumTypeData extends CommonTypeData {
  __typename: 'EnumConfigType';
  givenName: string;
}

interface RegularTypeData extends CommonTypeData {
  __typename: 'RegularConfigType';
  givenName: string;
}

interface ScalarUnionTypeData extends CommonTypeData {
  __typename: 'ScalarUnionConfigType';
  nonScalarTypeKey: string;
  scalarTypeKey: string;
}

export type TypeData =
  | CompositeTypeData
  | ListTypeData
  | NullableTypeData
  | RegularTypeData
  | EnumTypeData
  | ScalarUnionTypeData;

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
          <DictBlockComment indent={innerIndent} content={`One of the following:`} />
        )}
        {type.fields.map((fieldData) => (
          <DictEntry key={fieldData.name}>
            <DictBlockComment indent={innerIndent} content={fieldData.description} />
            {innerIndent}
            <DictKey theme={props.theme}>{fieldData.name}</DictKey>
            {!fieldData.isRequired && Optional}
            {`: `}
            {renderTypeRecursive(typeLookup[fieldData.configTypeKey], typeLookup, depth + 1, props)}
          </DictEntry>
        ))}
        {'  '.repeat(depth) + '}'}
      </>
    );
  }
  if (type.__typename === 'ArrayConfigType') {
    const ofTypeKey = type.typeParamKeys[0];
    return <>[{renderTypeRecursive(typeLookup[ofTypeKey], typeLookup, depth, props)}]</>;
  }
  if (type.__typename === 'NullableConfigType') {
    const ofTypeKey = type.typeParamKeys[0];
    return (
      <>
        {renderTypeRecursive(typeLookup[ofTypeKey], typeLookup, depth, props)}
        {Optional}
      </>
    );
  }

  if (type.__typename === 'ScalarUnionConfigType') {
    const nonScalarTypeMarkup = renderTypeRecursive(
      typeLookup[type.nonScalarTypeKey],
      typeLookup,
      depth,
      props,
    );
    const scalarTypeMarkup = renderTypeRecursive(
      typeLookup[type.scalarTypeKey],
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

export class ConfigTypeSchema extends React.PureComponent<ConfigTypeSchemaProps> {
  static fragments = {
    ConfigTypeSchemaFragment: gql`
      fragment ConfigTypeSchemaFragment on ConfigType {
        ... on EnumConfigType {
          givenName
        }
        ... on RegularConfigType {
          givenName
        }
        key
        description
        isSelector
        typeParamKeys
        ... on CompositeConfigType {
          fields {
            name
            description
            isRequired
            configTypeKey
          }
        }
        ... on ScalarUnionConfigType {
          scalarTypeKey
          nonScalarTypeKey
        }
      }
    `,
  };

  public render() {
    const {type, typesInScope} = this.props;

    const typeLookup = {};
    for (const typeInScope of typesInScope) {
      typeLookup[typeInScope.key] = typeInScope;
    }

    return (
      <TypeSchemaContainer>
        <DictBlockComment content={type.description} indent="" />
        {renderTypeRecursive(type, typeLookup, 0, this.props)}
      </TypeSchemaContainer>
    );
  }
}

const TypeSchemaContainer = styled.code`
  color: ${Colors.GRAY3};
  display: block;
  white-space: pre-wrap;
  font-size: smaller;
  line-height: 18px;
`;

const DictEntry = styled.div``;

const DictKey = styled.span<{theme: ConfigTypeSchemaTheme | undefined}>`
  color: ${({theme}) => (theme === 'dark' ? Colors.WHITE : Colors.BLACK)};
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

const Optional = <span style={{fontWeight: 500, color: Colors.ORANGE2}}>?</span>;
