import {Box, Button, Colors, Heading, Icon, TextInput} from '@dagster-io/ui-components';
import {useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {IntegrationIcon} from './IntegrationIcon';
import {IntegrationTag, IntegrationTagIcon, IntegrationTagLabel} from './IntegrationTag';
import {IntegrationConfig} from './types';

interface Props {
  integrations: IntegrationConfig[];
}

export const MarketplaceHome = (props: Props) => {
  const {integrations} = props;
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<IntegrationTag | null>(null);

  const filteredByTag = integrations.filter((integration) => {
    const {tags} = integration.frontmatter;
    return filters === null || tags.some((tag) => filters === tag);
  });

  const filteredIntegrations = filteredByTag.filter((integration) => {
    return integration.frontmatter.name.toLowerCase().includes(searchQuery.toLowerCase());
  });

  return (
    <Box flex={{direction: 'column', gap: 12}}>
      <Box margin={{bottom: 8}}>
        <Heading>Integrations Marketplace</Heading>
      </Box>
      <TextInput
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search for integrations"
        icon="search"
      />
      <Box
        flex={{direction: 'row', gap: 12, alignItems: 'center', wrap: 'wrap'}}
        margin={{bottom: 12}}
      >
        <div style={{fontSize: 16}}>Filters</div>
        {Object.values(IntegrationTag).map((tag) => (
          <Button
            key={tag}
            icon={<Icon name={IntegrationTagIcon[tag]} />}
            onClick={() => setFilters(filters === tag ? null : tag)}
            style={{backgroundColor: filters === tag ? Colors.backgroundBlue() : 'transparent'}}
          >
            {IntegrationTagLabel[tag]}
          </Button>
        ))}
      </Box>
      <IntegrationGrid>
        {filteredIntegrations.map((integration) => {
          const {
            frontmatter: {id, name, title},
            logo,
          } = integration;
          return (
            <CardLink key={id} to={`/integrations/${id}`}>
              <Box
                flex={{direction: 'row', gap: 16, alignItems: 'center'}}
                padding={{vertical: 16, horizontal: 12}}
                border="all"
                style={{borderRadius: 8, overflow: 'hidden'}}
              >
                <IntegrationIcon name={name} logo={logo} />
                <div style={{fontSize: 16, fontWeight: 600, flex: 1}}>{name || title}</div>
              </Box>
            </CardLink>
          );
        })}
      </IntegrationGrid>
    </Box>
  );
};

const CardLink = styled(Link)`
  white-space: normal;
  background-color: ${Colors.backgroundDefault()};
  transition: background-color 0.1s linear;
  color: ${Colors.textDefault()};
  text-decoration: none;
  border-radius: 8px;

  :hover {
    background-color: ${Colors.backgroundBlue()};
    color: ${Colors.textDefault()};
    text-decoration: none;
  }
`;

const IntegrationGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
`;
