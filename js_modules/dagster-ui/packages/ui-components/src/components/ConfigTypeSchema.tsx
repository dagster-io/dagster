import * as React from 'react';
import styled from 'styled-components';

import {
  colorAccentBlue,
  colorAccentPrimary,
  colorAccentReversed,
  colorAccentYellow,
  colorBackgroundLight,
  colorBackgroundLighter,
  colorBorderDefault,
  colorTextLighter,
  colorTextRed,
} from '../theme/color';

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

// Either type is guaranteed not to be undefined or if its possibly undefined
// then pass in the type name. This is a union to avoid called of ConfigEditorHelp from needing to pass a type name
// which doens't make sense at the root
type renderTypeRecursiveType = ((
  type: TypeData,
  typeLookup: {[typeName: string]: TypeData},
  depth: number,
  props: ConfigTypeSchemaProps,
  typeName?: string,
) => React.ReactElement<HTMLElement>) &
  ((
    type: TypeData | undefined,
    typeLookup: {[typeName: string]: TypeData},
    depth: number,
    props: ConfigTypeSchemaProps,
    typeName: string,
  ) => React.ReactElement<HTMLElement>);

const renderTypeRecursive: renderTypeRecursiveType = (type, typeLookup, depth, props, typeName) => {
  if (!type) {
    return (
      <span style={{color: colorTextRed(), opacity: 0.8}}>
        type &quot;{typeName}&quot; not found
      </span>
    );
  }
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
                  ? {borderBottom: `dashed ${colorAccentBlue()} 1px`, cursor: 'pointer'}
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
                typeLookup[fieldData.configTypeKey],
                typeLookup,
                depth + 1,
                props,
                fieldData.configTypeKey,
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
    return <>[{renderTypeRecursive(typeLookup[ofTypeKey], typeLookup, depth, props, ofTypeKey)}]</>;
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
          {renderTypeRecursive(typeLookup[keyTypeKey], typeLookup, depth + 1, props, keyTypeKey)}]
          {`: `}
          {renderTypeRecursive(
            typeLookup[valueTypeKey],
            typeLookup,
            depth + 1,
            props,
            valueTypeKey,
          )}
        </DictEntry>
        {'  '.repeat(depth) + '}'}
      </>
    );
  }

  if (type.__typename === 'NullableConfigType') {
    const ofTypeKey = type.typeParamKeys[0]!;
    return (
      <>
        {renderTypeRecursive(typeLookup[ofTypeKey], typeLookup, depth, props, ofTypeKey)}
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
      type.nonScalarTypeKey,
    );
    const scalarTypeMarkup = renderTypeRecursive(
      typeLookup[type.scalarTypeKey],
      typeLookup,
      depth,
      props,
      type.scalarTypeKey,
    );

    return (
      <span>
        {scalarTypeMarkup} | {nonScalarTypeMarkup}
      </span>
    );
  }

  return <span>{type.givenName}</span>;
};

export const tryPrettyPrintJSON = (jsonString: string) => {
  try {
    return JSON.stringify(JSON.parse(jsonString), null, 2);
  } catch (err) {
    // welp, looks like it's not valid JSON. This has happened at least once
    // in the wild - a user was able to build a metadata entry in Python with
    // a `NaN` number value: https://github.com/dagster-io/dagster/issues/8959
    return jsonString;
  }
};

const ConfigContent = React.memo(({value}: {value: string}) => (
  <>
    <ConfigHeader>
      <strong>Default value</strong>
    </ConfigHeader>
    <ConfigJSON>{tryPrettyPrintJSON(value)}</ConfigJSON>
  </>
));

const ConfigHeader = styled.div`
  background-color: ${colorAccentPrimary()};
  color: ${colorAccentReversed()};
  font-size: 13px;
  padding: 8px;
`;

const ConfigJSON = styled.pre`
  background-color: ${colorAccentPrimary()};
  color: ${colorAccentReversed()};
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
    <HoveredDictEntryContextProvider>
      <TypeSchemaContainer>
        <DictBlockComment content={type.description} indent="" />
        {renderTypeRecursive(type, typeLookup, 0, props)}
      </TypeSchemaContainer>
    </HoveredDictEntryContextProvider>
  );
});

const HoveredDictEntryContext = React.createContext<{
  useDictEntryHover: () => {hovered: boolean; onMouseEnter: () => void; onMouseLeave: () => void};
}>({
  useDictEntryHover() {
    return {hovered: false, onMouseEnter: () => {}, onMouseLeave: () => {}};
  },
});

/**
 * Very cheap way to make sure only 1 dict entry is hovered at a time.
 * We simply record the unhover function for thast hovered dict entry and call it whenever
 * a new dict entry is hovered. This is cheaper than updating every dict entry via context
 * because we don't cause every dict entry to re-render. Only the two being hovered/unhovered.
 */
const HoveredDictEntryContextProvider = React.memo(({children}: {children: React.ReactNode}) => {
  const value = React.useMemo(() => {
    // We need to keep a stack of the entries that are hovered because they are nested.
    // The `MouseEnter` handler only fires when we first hover the entry, but it does not
    // fire when exiting a nested dict entry because technically we never left.
    // To handle that case whenever we `MouseLeave` fires we restore the last element in the
    // stack before the leaving element as hovered
    let currentHoveredStack: Array<{setHovered: (hovered: boolean) => void}> = [];

    function useDictEntryHover() {
      const [hovered, setHovered] = React.useState(false);
      const self = React.useMemo(() => ({setHovered}), []);
      return {
        hovered,

        // Unset the previous hovered target and set the current one
        onMouseEnter: React.useCallback(() => {
          const lastHovered = currentHoveredStack[currentHoveredStack.length - 1];
          if (lastHovered) {
            // If there is already a hovered element, unhover it.
            lastHovered.setHovered(false);
          }
          // Record that we're now the last entry to be hovered
          currentHoveredStack.push(self);
          setHovered(true);
        }, [self]),

        // Unset the current hovered target and use its parent as the next hovered target if it has one
        onMouseLeave: React.useCallback(() => {
          const lastHovered = currentHoveredStack[currentHoveredStack.length - 1];
          if (!lastHovered) {
            // This should never happen since we can't MouseLeave something we never MouseEnter'd
            // We should be the last hovered element since events bubble up
            return;
          }
          // Unhover the current element
          lastHovered.setHovered(false);

          // Find the index of this element and remove it.
          // There shouldn't be anything after it since MouseLeave events should bubble upwards
          const currentIndex = currentHoveredStack.indexOf(self);
          if (currentIndex !== -1) {
            // This should only remove 1 entry, the last hovered entry
            currentHoveredStack = currentHoveredStack.slice(0, currentIndex);
          }

          // If something is still on the stack after this dict entry is no longer hovered then
          // its a parent dict entry and should be hovered
          const nextLastHovered = currentHoveredStack[currentHoveredStack.length - 1];
          if (nextLastHovered) {
            nextLastHovered.setHovered(true);
          }
        }, [self]),
      };
    }
    return {useDictEntryHover};
  }, []);
  return (
    <HoveredDictEntryContext.Provider value={value}>{children}</HoveredDictEntryContext.Provider>
  );
});

const DictEntry = React.forwardRef(
  (
    props: React.ComponentProps<typeof DictEntryDiv>,
    ref: React.ForwardedRef<HTMLButtonElement>,
  ) => {
    const {hovered, onMouseEnter, onMouseLeave} =
      React.useContext(HoveredDictEntryContext).useDictEntryHover();

    return (
      <DictEntryDiv2>
        <DictEntryDiv
          {...props}
          $hovered={hovered}
          onMouseEnter={onMouseEnter}
          onMouseLeave={onMouseLeave}
          ref={ref}
        />
      </DictEntryDiv2>
    );
  },
);

const DictEntryDiv2 = styled.div``;
const DictEntryDiv = styled.div<{$hovered: boolean}>`
  border: 1px solid transparent;

  ${({$hovered}) =>
    $hovered
      ? `
      border: 1px solid ${colorBorderDefault()};
      background-color: ${colorBackgroundLight()};
      >${DictEntryDiv2} {
        background-color: ${colorBackgroundLighter()};
      }
    `
      : ``}
  }
`;

const TypeSchemaContainer = styled.code`
  color: ${colorTextLighter()};
  display: block;
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 18px;
`;

const DictKey = styled.span<{theme: ConfigTypeSchemaTheme | undefined}>`
  color: ${({theme}) => (theme === 'dark' ? colorAccentReversed() : colorAccentPrimary())};
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

const Optional = <span style={{fontWeight: 500, color: colorAccentYellow()}}>?</span>;
