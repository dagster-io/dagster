import {Colors} from '@blueprintjs/core';
import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled, {createGlobalStyle} from 'styled-components';

import {LeftNavSimple} from 'src/nav/LeftNavSimple';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Table} from 'src/ui/Table';
import {Heading} from 'src/ui/Text';

const BodyReset = createGlobalStyle`
  body {
    padding: 0 !important;
    margin: 0 !important;
    height: 100vh;
  }

  #root {
    height: 100%;
  }
`;

// eslint-disable-next-line import/no-default-export
export default {
  title: 'LeftNavSimple',
  component: LeftNavSimple,
} as Meta;

const PIPELINES = new Array(12)
  .fill(null)
  .map(() => faker.random.words(2).toLowerCase().replace(' ', '-'));

const REPO_ONE = `${faker.random.word()}@${faker.random.words(2)}`.toLowerCase().replace(' ', '-');
const REPO_TWO = `${faker.random.word()}@${faker.random.words(2)}`.toLowerCase().replace(' ', '-');

export const Default = () => (
  <ApolloTestProvider>
    <BodyReset />
    <div style={{height: '100%', display: 'flex', flexDirection: 'row'}}>
      <LeftNavSimple />
      <div style={{flexGrow: 1, overflowY: 'auto'}}>
        <Box padding={{vertical: 20, horizontal: 24}}>
          <Group direction="column" spacing={16}>
            <Heading>Pipelines</Heading>
            <input
              type="text"
              placeholder="Filter…"
              style={{
                border: `1px solid ${Colors.LIGHT_GRAY1}`,
                borderRadius: '2px',
                padding: '8px',
                width: '500px',
              }}
            />
            <Table>
              <thead>
                <tr>
                  <th style={{width: '30%'}}>Pipeline</th>
                  <th style={{width: '40%'}}>Repository</th>
                  <th>Recent runs</th>
                </tr>
              </thead>
              <tbody>
                {PIPELINES.map((pipeline) => (
                  <tr key={pipeline}>
                    <td>
                      <Link to={`/pipelines/${pipeline}`}>{pipeline}</Link>
                    </td>
                    <td>{Math.random() > 0.3 ? REPO_ONE : REPO_TWO}</td>
                    <td>
                      <Group direction="row" spacing={4} alignItems="center">
                        {new Array(5).fill(null).map((_, ii) => (
                          <Dot key={ii} $value={Math.random()} />
                        ))}
                      </Group>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Group>
        </Box>
      </div>
    </div>
  </ApolloTestProvider>
);

interface DotProps {
  $value: number;
}

const Dot = styled.div<DotProps>`
  height: 12px;
  width: 12px;
  border-radius: 6px;
  background-color: ${({$value}) => ($value > 0.3 ? Colors.GREEN5 : Colors.RED5)};
`;
