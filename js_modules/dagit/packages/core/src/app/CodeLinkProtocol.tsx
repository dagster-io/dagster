import {MenuItem, Menu, Select, TextInput, Box, Button, Icon, CaptionMono} from '@dagster-io/ui';
import * as React from 'react';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

export const CodeLinkProtocolKey = 'CodeLinkProtocolPreference';

const POPULAR_PROTOCOLS = {
  'vscode://file/{FILE}:{LINE}': 'Visual Studio Code',
  '': 'Custom',
};

const DEFAULT_PROTOCOL = {protocol: Object.keys(POPULAR_PROTOCOLS)[0], custom: false};

type ProtocolData = {
  protocol: string;
  custom: boolean;
};

export const CodeLinkProtocolContext = React.createContext<
  [ProtocolData, React.Dispatch<React.SetStateAction<ProtocolData | undefined>>]
>([DEFAULT_PROTOCOL, () => '']);

export const CodeLinkProtocolProvider: React.FC = (props) => {
  const state = useStateWithStorage<ProtocolData>(CodeLinkProtocolKey, (x) =>
    x === undefined ? DEFAULT_PROTOCOL : x,
  );

  return (
    <CodeLinkProtocolContext.Provider value={state}>
      {props.children}
    </CodeLinkProtocolContext.Provider>
  );
};

export const CodeLinkProtocolSelect: React.FC = ({}) => {
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
          modifiers: {offset: {enabled: true, offset: '-12px, 8px'}},
        }}
        activeItem={isCustom ? '' : codeLinkProtocol.protocol}
        inputProps={{style: {width: '300px'}}}
        items={Object.keys(POPULAR_PROTOCOLS)}
        itemPredicate={(query, protocol) => protocol.toLowerCase().includes(query.toLowerCase())}
        itemRenderer={(protocol, props) => (
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
        onItemSelect={(protocol) => setCodeLinkProtocol({protocol, custom: protocol === ''})}
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
        ></TextInput>
      ) : (
        <Box padding={{left: 8, top: 2}}>
          <CaptionMono>{codeLinkProtocol.protocol}</CaptionMono>
        </Box>
      )}
    </Box>
  );
};
