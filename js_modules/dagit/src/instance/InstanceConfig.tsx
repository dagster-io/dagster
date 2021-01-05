import {gql, useQuery} from '@apollo/client';
import {Colors, Spinner} from '@blueprintjs/core';
import * as React from 'react';
import {createGlobalStyle} from 'styled-components/macro';

import {HighlightedCodeBlock} from 'src/HighlightedCodeBlock';
import {InstanceConfigQuery} from 'src/instance/types/InstanceConfigQuery';
import {Group} from 'src/ui/Group';
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

export const InstanceConfig = () => {
  const {data} = useQuery<InstanceConfigQuery>(INSTANCE_CONFIG_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  return data ? (
    <Group direction="column" spacing={12}>
      <Subheading>{`Dagster ${data.version}`}</Subheading>
      <YamlShimStyle />
      <HighlightedCodeBlock value={data.instance.info} language="yaml" />
    </Group>
  ) : (
    <Spinner size={35} />
  );
};

export const INSTANCE_CONFIG_QUERY = gql`
  query InstanceConfigQuery {
    version
    instance {
      info
    }
  }
`;
