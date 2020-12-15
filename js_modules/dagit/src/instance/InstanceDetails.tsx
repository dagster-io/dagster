import {gql, useQuery} from '@apollo/client';
import {Colors, Spinner} from '@blueprintjs/core';
import * as React from 'react';
import {createGlobalStyle} from 'styled-components/macro';

import {HighlightedCodeBlock} from 'src/HighlightedCodeBlock';
import {InstanceDetailsQuery} from 'src/instance/types/InstanceDetailsQuery';
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

export const InstanceDetails: React.FC = () => {
  const {data} = useQuery<InstanceDetailsQuery>(INSTANCE_DETAILS_QUERY, {
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

const INSTANCE_DETAILS_QUERY = gql`
  query InstanceDetailsQuery {
    version
    instance {
      info
    }
  }
`;
