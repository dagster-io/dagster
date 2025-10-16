import {HTMLProps, useCallback, useState} from 'react';

import {BaseButton} from '../BaseButton';
import {Box} from '../Box';
import {Button} from '../Button';
import {Colors} from '../Color';
import {HorizontalControls} from '../HorizontalControls';
import {Icon} from '../Icon';
import {ListItem} from '../ListItem';
import {Menu, MenuItem} from '../Menu';
import {Popover} from '../Popover';
import {Caption} from '../Text';
import {Tooltip} from '../Tooltip';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'ListItem',
  component: ListItem,
};

export const Default = () => {
  return (
    <div style={{width: '600px'}}>
      <ListItem
        index={0}
        renderLink={renderLink}
        href="/jobs/foo"
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <Icon name="job" />
            foo
          </Box>
        }
        right={<div>Right</div>}
      />
      <ListItem
        index={1}
        renderLink={renderLink}
        href="/jobs/bar"
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <Icon name="job" />
            bar
          </Box>
        }
        right={<div>Right</div>}
      />
      <ListItem
        index={2}
        renderLink={renderLink}
        href="/jobs/baz"
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <Icon name="job" />
            baz
          </Box>
        }
        right={<div>Right</div>}
      />
    </div>
  );
};

type AutomationType = 'sensor' | 'schedule' | 'none';

const AutomationButton = ({type, enabled = false}: {type: AutomationType; enabled?: boolean}) => {
  const icon = () => {
    if (type === 'none') {
      return <Icon name="status" color={Colors.accentGray()} />;
    }

    return <Icon name={type} color={enabled ? Colors.accentGreen() : Colors.accentGray()} />;
  };

  return (
    <BaseButton
      icon={icon()}
      iconColor={enabled && type !== 'none' ? Colors.accentGreen() : Colors.accentGray()}
      fillColor="transparent"
      fillColorHover={Colors.backgroundLightHover()}
      strokeColor="transparent"
      strokeColorHover="transparent"
    />
  );
};

const renderLink = (props: HTMLProps<HTMLAnchorElement>) => <a {...props} />;

export const JobList = () => {
  const [checkedItems, setCheckedItems] = useState<Set<string>>(() => new Set());

  const onToggle = useCallback((item: string) => {
    setCheckedItems((current) => {
      const copy = new Set(current);
      if (copy.has(item)) {
        copy.delete(item);
      } else {
        copy.add(item);
      }
      return copy;
    });
  }, []);

  return (
    <div style={{width: '100%'}}>
      <ListItem
        index={0}
        renderLink={renderLink}
        checked={checkedItems.has('foo')}
        onToggle={() => onToggle('foo')}
        href="/jobs/foo"
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <Icon name="job" />
            foo
          </Box>
        }
        right={
          <HorizontalControls
            controls={[
              {
                key: 'latest-run',
                control: (
                  <Tooltip content="Hello" placement="top">
                    <Button intent="none">2 mins ago</Button>
                  </Tooltip>
                ),
              },
              {
                key: 'automations',
                control: (
                  <Tooltip content="Hello" placement="top">
                    <AutomationButton type="sensor" enabled />
                  </Tooltip>
                ),
              },
              {
                key: 'menu',
                control: (
                  <Popover
                    content={
                      <Menu>
                        <MenuItem text="View job" />
                      </Menu>
                    }
                    placement="bottom-end"
                  >
                    <Button intent="none" icon={<Icon name="more_horiz" />} />
                  </Popover>
                ),
              },
            ]}
          />
        }
      />
      <ListItem
        index={1}
        renderLink={renderLink}
        checked={checkedItems.has('bar')}
        onToggle={() => onToggle('bar')}
        href="/jobs/bar"
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <Icon name="job" />
            bar
          </Box>
        }
        right={
          <HorizontalControls
            controls={[
              {
                key: 'latest-run',
                control: (
                  <Tooltip content="Hello" placement="top">
                    <Button intent="none">2 mins ago</Button>
                  </Tooltip>
                ),
              },
              {
                key: 'automations',
                control: (
                  <Tooltip content="Hello" placement="top">
                    <AutomationButton type="schedule" enabled />
                  </Tooltip>
                ),
              },
              {
                key: 'menu',
                control: (
                  <Popover
                    content={
                      <Menu>
                        <MenuItem text="View job" />
                      </Menu>
                    }
                    placement="bottom-end"
                  >
                    <Button intent="none" icon={<Icon name="more_horiz" />} />
                  </Popover>
                ),
              },
            ]}
          />
        }
      />
      <ListItem
        index={2}
        renderLink={renderLink}
        checked={checkedItems.has('baz')}
        onToggle={() => onToggle('baz')}
        href="/jobs/baz"
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <Icon name="job" />
            baz
          </Box>
        }
        right={
          <HorizontalControls
            controls={[
              {
                key: 'latest-run',
                control: (
                  <Tooltip content="Hello" placement="top">
                    <Button intent="none">2 mins ago</Button>
                  </Tooltip>
                ),
              },
              {
                key: 'automations',
                control: (
                  <Tooltip content="Hello" placement="top">
                    <AutomationButton type="sensor" />
                  </Tooltip>
                ),
              },
              {
                key: 'menu',
                control: (
                  <Popover
                    content={
                      <Menu>
                        <MenuItem text="View job" />
                      </Menu>
                    }
                    placement="bottom-end"
                  >
                    <Button intent="none" icon={<Icon name="more_horiz" />} />
                  </Popover>
                ),
              },
            ]}
          />
        }
      />
      <ListItem
        index={3}
        renderLink={renderLink}
        href="/jobs/gorp"
        checked={checkedItems.has('gorp')}
        onToggle={() => onToggle('gorp')}
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <Icon name="job" />
            gorp
          </Box>
        }
        right={
          <HorizontalControls
            controls={[
              {
                key: 'latest-run',
                control: (
                  <Tooltip content="Hello" placement="top">
                    <Button intent="none">1 hour ago</Button>
                  </Tooltip>
                ),
              },
              {
                key: 'automations',
                control: (
                  <Tooltip content="Hello" placement="top">
                    <AutomationButton type="none" />
                  </Tooltip>
                ),
              },
              {
                key: 'menu',
                control: (
                  <Popover
                    content={
                      <Menu>
                        <MenuItem text="View job" />
                      </Menu>
                    }
                    placement="bottom-end"
                  >
                    <Button intent="none" icon={<Icon name="more_horiz" />} />
                  </Popover>
                ),
              },
            ]}
          />
        }
      />
      <ListItem
        index={4}
        renderLink={renderLink}
        href="/jobs/multi-line"
        checked={checkedItems.has('multi-line')}
        onToggle={() => onToggle('multi-line')}
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'flex-start'}}>
            <Box margin={{top: 2}}>
              <Icon name="job" />
            </Box>
            <Box flex={{direction: 'column', gap: 4}}>
              <div>multi-line</div>
              <Caption>
                This is a description of this job, with maybe some metadata like the status or
                something.
              </Caption>
            </Box>
          </Box>
        }
        right={
          <HorizontalControls
            controls={[
              {
                key: 'latest-run',
                control: (
                  <Tooltip content="Hello" placement="top">
                    <Button intent="none">3 hours ago</Button>
                  </Tooltip>
                ),
              },
              {
                key: 'automations',
                control: (
                  <Tooltip content="Hello" placement="top">
                    <AutomationButton type="none" />
                  </Tooltip>
                ),
              },
              {
                key: 'menu',
                control: (
                  <Popover
                    content={
                      <Menu>
                        <MenuItem text="View job" />
                      </Menu>
                    }
                    placement="bottom-end"
                  >
                    <Button intent="none" icon={<Icon name="more_horiz" />} />
                  </Popover>
                ),
              },
            ]}
          />
        }
      />
    </div>
  );
};

export const SmallList = () => {
  return (
    <div style={{width: '400px'}}>
      <ListItem
        index={0}
        padding={{vertical: 8, horizontal: 12}}
        renderLink={renderLink}
        href="/jobs/foo"
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <Icon name="job" />
            foo
          </Box>
        }
        right={<div>Right</div>}
      />
      <ListItem
        index={1}
        padding={{vertical: 8, horizontal: 12}}
        renderLink={renderLink}
        href="/jobs/bar"
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <Icon name="job" />
            bar
          </Box>
        }
        right={<div>Right</div>}
      />
      <ListItem
        index={2}
        padding={{vertical: 8, horizontal: 12}}
        renderLink={renderLink}
        href="/jobs/baz"
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <Icon name="job" />
            baz
          </Box>
        }
        right={<div>Right</div>}
      />
    </div>
  );
};

export const BigPadding = () => {
  return (
    <div style={{width: '400px'}}>
      <ListItem
        index={0}
        padding={{vertical: 48, horizontal: 48}}
        renderLink={renderLink}
        href="/jobs/foo"
        left={<div>Left</div>}
        right={
          <HorizontalControls
            controls={[
              {key: 'menu', control: <Button intent="none" icon={<Icon name="more_horiz" />} />},
            ]}
          />
        }
      />
    </div>
  );
};
