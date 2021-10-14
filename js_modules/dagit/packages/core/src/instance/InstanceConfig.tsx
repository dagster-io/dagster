import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {Link, useHistory} from 'react-router-dom';
import styled, {createGlobalStyle, css} from 'styled-components/macro';

import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {HighlightedCodeBlock} from '../ui/HighlightedCodeBlock';
import {IconWIP} from '../ui/Icon';
import {PageHeader} from '../ui/PageHeader';
import {Spinner} from '../ui/Spinner';
import {Code, Heading, Subheading} from '../ui/Text';

import {InstanceTabs} from './InstanceTabs';
import {InstanceConfigQuery} from './types/InstanceConfigQuery';

const YamlShimStyle = createGlobalStyle`
  .hljs.yaml {
    margin: 0;
    padding: 0;
  }

  .config-yaml {
    .hljs-attr {
      color: ${ColorsWIP.Blue700};
    }

    .hljs-string {
      color: ${ColorsWIP.Green700};
    }

    .hljs-number {
      color: ${ColorsWIP.Red700};
    }
  }
`;

export const InstanceConfig = React.memo(() => {
  const history = useHistory();
  const {data} = useQuery<InstanceConfigQuery>(INSTANCE_CONFIG_QUERY, {
    fetchPolicy: 'cache-and-network',
  });
  const [hash, setHash] = React.useState(() => document.location.hash);

  React.useEffect(() => {
    // Once data has finished loading and rendering, scroll to hash
    if (data) {
      const documentHash = document.location.hash;
      if (documentHash) {
        const target = documentHash.slice(1);
        document.getElementById(target)?.scrollIntoView({
          block: 'start',
          inline: 'nearest',
        });
      }
    }
  }, [data]);

  React.useEffect(() => {
    const unlisten = history.listen((location) => {
      setHash(location.hash);
    });

    return () => unlisten();
  }, [history]);

  if (!data) {
    return (
      <Box padding={{vertical: 64}}>
        <Spinner purpose="section" />
      </Box>
    );
  }

  // Split by top-level yaml keys
  const sections = data.instance.info.split(/\n(?=\w)/g);

  return (
    <>
      <PageHeader title={<Heading>Instance status</Heading>} tabs={<InstanceTabs tab="config" />} />
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
      >
        <Subheading>
          Dagster version: <Code style={{fontSize: '16px'}}>{data.version}</Code>
        </Subheading>
      </Box>
      <YamlShimStyle />
      <Box padding={{vertical: 16, horizontal: 24}}>
        {sections.map((section) => {
          const [id] = section.split(/\:/);
          const hashForSection = `#${id}`;
          return (
            <Box
              flex={{direction: 'row', alignItems: 'flex-start'}}
              padding={{vertical: 8}}
              key={id}
              id={id}
            >
              <ConfigLink to={`/instance/config${hashForSection}`} key={id}>
                <IconWIP name="link" color={ColorsWIP.Gray300} />
              </ConfigLink>
              <ConfigSection highlighted={hash === hashForSection}>
                <HighlightedCodeBlock value={section} language="yaml" className="config-yaml" />
              </ConfigSection>
            </Box>
          );
        })}
      </Box>
    </>
  );
});

const ConfigLink = styled(Link)`
  margin-right: 12px;
  margin-top: 2px;
  user-select: none;
  transition: filter ease-in-out 100ms;

  &:hover {
    filter: brightness(0.4);
  }
`;

const ConfigSection = styled.div<{highlighted: boolean}>`
  flex-grow: 1;

  ${({highlighted}) =>
    highlighted
      ? css`
          background-color: ${ColorsWIP.Gray100};
          margin: -8px;
          padding: 8px;
        `
      : null};
`;

export const INSTANCE_CONFIG_QUERY = gql`
  query InstanceConfigQuery {
    version
    instance {
      info
    }
  }
`;
