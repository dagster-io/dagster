import clsx from 'clsx';
import * as React from 'react';

import {Colors} from './Color';
import {Popover} from './Popover';
import {ConfigSchema_allConfigTypes as TypeData} from './configeditor/types/ConfigSchema';
import styles from './css/ConfigTypeSchema.module.css';

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
      <span style={{color: Colors.textRed(), opacity: 0.8}}>
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
            <span
              className={props.theme === 'dark' ? styles.dictKeyDark : styles.dictKeyLight}
              style={
                fieldData.defaultValueAsJson
                  ? {borderBottom: `dashed ${Colors.accentBlue()} 1px`, cursor: 'pointer'}
                  : undefined
              }
            >
              {fieldData.name}
            </span>
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
    const ofTypeKey = type.typeParamKeys[0] ?? '';
    return <>[{renderTypeRecursive(typeLookup[ofTypeKey], typeLookup, depth, props, ofTypeKey)}]</>;
  }

  if (type.__typename === 'MapConfigType') {
    // e.g.
    // {
    //   [name_hint: String]: Int
    // }
    const keyTypeKey = type.typeParamKeys[0] ?? '';
    const valueTypeKey = type.typeParamKeys[1] ?? '';
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
    const ofTypeKey = type.typeParamKeys[0] ?? '';
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
  } catch {
    // welp, looks like it's not valid JSON. This has happened at least once
    // in the wild - a user was able to build a metadata entry in Python with
    // a `NaN` number value: https://github.com/dagster-io/dagster/issues/8959
    return jsonString;
  }
};

const ConfigContent = React.memo(({value}: {value: string}) => (
  <>
    <div className={styles.configHeader}>
      <strong>Default value</strong>
    </div>
    <pre className={styles.configJSON}>{tryPrettyPrintJSON(value)}</pre>
  </>
));

export const ConfigTypeSchema = React.memo((props: ConfigTypeSchemaProps) => {
  const {type, typesInScope} = props;

  const typeLookup: Record<string, TypeData> = {};
  for (const typeInScope of typesInScope) {
    typeLookup[typeInScope.key] = typeInScope;
  }

  return (
    <HoveredDictEntryContextProvider>
      <code className={styles.typeSchemaContainer}>
        <DictBlockComment content={type.description} indent="" />
        {renderTypeRecursive(type, typeLookup, 0, props)}
      </code>
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

const DictEntry = (props: React.HTMLAttributes<HTMLDivElement>) => {
  const {hovered, onMouseEnter, onMouseLeave} =
    React.useContext(HoveredDictEntryContext).useDictEntryHover();

  return (
    <div
      {...props}
      className={clsx(styles.dictEntry, hovered && styles.hovered)}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    />
  );
};

const DictBlockComment = ({indent = '', content}: {indent: string; content: string | null}) =>
  content !== null && content !== '' ? (
    <div className={styles.dictComment}>{`${indent.replace(/ /g, '\u00A0')}/* ${content} */`}</div>
  ) : null;

const Optional = <span style={{fontWeight: 500, color: Colors.accentYellow()}}>?</span>;
