import {
  Box,
  Button,
  CaptionMono,
  Icon,
  Menu,
  MenuItem,
  Select,
  TextInput,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

export const CodeLinkProtocolKey = 'CodeLinkProtocolPreference';

const POPULAR_PROTOCOLS: {[name: string]: string} = {
  'vscode://file/{FILE}:{LINE}': 'Visual Studio Code',
  '': 'Custom',
};

const DEFAULT_PROTOCOL = {protocol: Object.keys(POPULAR_PROTOCOLS)[0]!, custom: false};

export type ProtocolData = {
  protocol: string;
  custom: boolean;
};

export const CodeLinkProtocolContext = React.createContext<
  ReturnType<typeof useStateWithStorage<ProtocolData>>
>([DEFAULT_PROTOCOL, () => '', () => {}]);

export const CodeLinkProtocolProvider = ({children}: {children: React.ReactNode}) => {
  const state = useStateWithStorage<ProtocolData>(
    CodeLinkProtocolKey,
    (x) => x ?? DEFAULT_PROTOCOL,
  );

  return (
    <CodeLinkProtocolContext.Provider value={state}>{children}</CodeLinkProtocolContext.Provider>
  );
};

export const CodeLinkProtocolSelect = ({}) => {
  const [codeLinkProtocol, setCodeLinkProtocol] = React.useContext(CodeLinkProtocolContext);
  const isCustom = codeLinkProtocol.custom;

  return (
    <Box
      flex={{direction: 'column', gap: 4, alignItems: 'stretch'}}
      style={{width: 225, height: 55}}
    >
      <Select<string>
        popoverProps={{
          position: 'bottom-left',
          modifiers: {offset: {enabled: true, options: {offset: [-12, 8]}}},
        }}
        activeItem={isCustom ? '' : codeLinkProtocol.protocol}
        inputProps={{style: {width: '300px'}}}
        items={Object.keys(POPULAR_PROTOCOLS)}
        itemPredicate={(query: string, protocol: string) =>
          protocol.toLowerCase().includes(query.toLowerCase())
        }
        itemRenderer={(protocol: string, props: any) => (
          <MenuItem
            active={props.modifiers.active}
            onClick={props.handleClick}
            label={protocol}
            key={protocol}
            text={POPULAR_PROTOCOLS[protocol]}
          />
        )}
        itemListRenderer={({renderItem, filteredItems}) => {
          const renderedItems = filteredItems.map(renderItem).filter(Boolean);
          return <Menu>{renderedItems}</Menu>;
        }}
        noResults={<MenuItem disabled text="No results." />}
        onItemSelect={(protocol: string) =>
          setCodeLinkProtocol({protocol, custom: protocol === ''})
        }
      >
        <Button rightIcon={<Icon name="expand_more" />} style={{width: '225px'}}>
          <div style={{width: '225px', textAlign: 'left'}}>
            {isCustom ? 'Custom' : POPULAR_PROTOCOLS[codeLinkProtocol.protocol]}
          </div>
        </Button>
      </Select>
      {isCustom ? (
        <TextInput
          value={codeLinkProtocol.protocol}
          onChange={(e) =>
            setCodeLinkProtocol({
              protocol: e.target.value,
              custom: true,
            })
          }
          placeholder="protocol://{FILE}:{LINE}"
        />
      ) : (
        <Box padding={{left: 8, top: 2}}>
          <CaptionMono>{codeLinkProtocol.protocol}</CaptionMono>
        </Box>
      )}
    </Box>
  );
};
