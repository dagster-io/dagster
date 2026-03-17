import {Box} from '../Box';
import {Button} from '../Button';
import {PageHeader} from '../PageHeader';
import {Tab, Tabs} from '../Tabs';
import {Tag} from '../Tag';
import {Subtitle1} from '../Text';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'PageHeader',
  component: PageHeader,
};

export const Default = () => {
  return <PageHeader title={<Subtitle1>My Page Title</Subtitle1>} />;
};

export const WithTagsAndActions = () => {
  return (
    <PageHeader
      title={<Subtitle1>My Page Title</Subtitle1>}
      tags={
        <Box flex={{direction: 'row', gap: 8}}>
          <Tag>Production</Tag>
          <Tag>Healthy</Tag>
        </Box>
      }
      right={
        <Box flex={{direction: 'row', gap: 8}}>
          <Button>Reload</Button>
          <Button intent="primary">Launch Run</Button>
        </Box>
      }
    />
  );
};

export const WithTabs = () => {
  return (
    <PageHeader
      title={<Subtitle1>My Page Title</Subtitle1>}
      tags={<Tag>Production</Tag>}
      right={<Button intent="primary">Launch Run</Button>}
      tabs={
        <Tabs selectedTabId="overview">
          <Tab id="overview" title="Overview" />
          <Tab id="partitions" title="Partitions" />
          <Tab id="config" title="Config" />
        </Tabs>
      }
    />
  );
};
