import {Box} from '../Box';
import {Colors} from '../Color';
import {Group} from '../Group';
import {Spinner} from '../Spinner';
import {Caption, Code} from '../Text';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Spinner',
  component: Spinner,
};

export const Sizes = () => {
  return (
    <Group direction="column" spacing={32}>
      <Box padding={20} border="all">
        <Group direction="column" spacing={16}>
          <Code>purpose=&quot;caption-text&quot;</Code>
          <Group direction="row" spacing={8} alignItems="center">
            <Spinner purpose="caption-text" />
            <Caption>Waiting for something to load…</Caption>
          </Group>
        </Group>
      </Box>
      <Box padding={20} border="all">
        <Group direction="column" spacing={16}>
          <Code>purpose=&quot;body-text&quot;</Code>
          <Group direction="row" spacing={8} alignItems="center">
            <Spinner purpose="body-text" />
            <div>Waiting for something to load…</div>
          </Group>
        </Group>
      </Box>
      <Box padding={20} border="all">
        <Group direction="column" spacing={16}>
          <Code>purpose=&quot;section&quot;</Code>
          <Box flex={{direction: 'row', justifyContent: 'center', gap: 10}} padding={24}>
            <Spinner purpose="section" />
            <Spinner purpose="section" fillColor={Colors.accentBlue()} />
          </Box>
        </Group>
      </Box>
      <Box padding={20} border="all">
        <Group direction="column" spacing={16}>
          <Code>purpose=&quot;page&quot;</Code>
          <Box flex={{direction: 'row', justifyContent: 'center', gap: 10}} padding={48}>
            <Spinner purpose="page" />
            <Spinner purpose="page" fillColor={Colors.accentBlue()} />
          </Box>
        </Group>
      </Box>
    </Group>
  );
};
