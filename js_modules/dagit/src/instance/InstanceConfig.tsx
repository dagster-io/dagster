import {gql, useQuery} from '@apollo/client';
import {Colors, Icon} from '@blueprintjs/core';
import * as React from 'react';
import {Link, useHistory} from 'react-router-dom';
import styled, {createGlobalStyle, css} from 'styled-components';

import {InstanceConfigQuery} from 'src/instance/types/InstanceConfigQuery';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {HighlightedCodeBlock} from 'src/ui/HighlightedCodeBlock';
import {Spinner} from 'src/ui/Spinner';
import {Subheading} from 'src/ui/Text';

const YamlShimStyle = createGlobalStyle`
  .hljs.yaml {
    margin: 0;
    padding: 0;
  }

  .hljs-attr {
    color: ${Colors.BLUE1};
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
    return <Spinner purpose="section" />;
  }

  // Split by top-level yaml keys
  const sections = data.instance.info.split(/\n(?=\w)/g);

  return (
    <Group direction="column" spacing={16}>
      <Subheading>{`Dagster ${data.version}`}</Subheading>
      <YamlShimStyle />
      {sections.map((section) => {
        const [id] = section.split(/\:/);
        const hashForSection = `#${id}`;
        return (
          <Box flex={{direction: 'row', alignItems: 'flex-start'}} key={id} id={id}>
            <ConfigLink to={`/instance/config${hashForSection}`} key={id}>
              <Icon icon="link" color={Colors.GRAY4} iconSize={11} />
            </ConfigLink>
            <ConfigSection highlighted={hash === hashForSection}>
              <HighlightedCodeBlock value={section} language="yaml" />
            </ConfigSection>
          </Box>
        );
      })}
    </Group>
  );
});

const ConfigLink = styled(Link)`
  margin-right: 12px;
  margin-top: -1px;
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
          background-color: ${Colors.LIGHT_GRAY3};
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
