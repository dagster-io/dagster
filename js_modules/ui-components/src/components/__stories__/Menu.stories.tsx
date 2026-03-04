import {useCallback, useState} from 'react';
import styled from 'styled-components';

import {Box} from '../Box';
import {Checkbox} from '../Checkbox';
import {Colors} from '../Color';
import {
  Menu,
  MenuDivider,
  MenuExternalLink,
  MenuItem,
  MenuItemForInteractiveContent,
} from '../Menu';
import {Spinner} from '../Spinner';
import {Tooltip} from '../Tooltip';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Menu',
  component: Menu,
};

export const Default = () => {
  return (
    <Box flex={{direction: 'column', gap: 8}} padding={8}>
      <Container style={{width: '180px'}}>
        <Menu>
          <MenuItem text="Item 01" />
          <MenuItem text="Item 02" />
          <MenuItem text="Item 03" />
        </Menu>
      </Container>
      <Container style={{width: '180px'}}>
        <Menu>
          <MenuItem icon="folder" text="Item 01" />
          <MenuItem icon="location_on" text="Item 02" />
          <MenuItem icon="download_for_offline" text="Item 03" />
          <MenuDivider />
          <MenuItem icon="attach_file" text="Item 04" />
        </Menu>
      </Container>
      <Container style={{width: '180px'}}>
        <Menu>
          <MenuItem icon="download_for_offline" text="Save" />
          <MenuItem icon="attach_file" text="Attach" />
          <MenuItem intent="danger" icon="delete" text="Delete" />
        </Menu>
      </Container>
      <Container style={{width: '180px'}}>
        <Menu>
          <MenuDivider title="Here you can save" />
          <MenuItem icon="download_for_offline" text="Save" />
          <MenuDivider title="Here you can attach" />
          <MenuItem icon="attach_file" text="Attach" />
          <MenuDivider title="Here you can delete" />
          <MenuItem intent="danger" icon="delete" text="Delete" />
        </Menu>
      </Container>
    </Box>
  );
};

export const AllIntents = () => {
  return (
    <Box flex={{direction: 'column', gap: 8}} padding={8}>
      <Container style={{width: '200px'}}>
        <Menu>
          <MenuItem icon="check_circle" intent="success" text="Success Action" />
          <MenuItem icon="info" intent="primary" text="Primary Action" />
          <MenuItem icon="warning" intent="warning" text="Warning Action" />
          <MenuItem icon="error" intent="danger" text="Danger Action" />
          <MenuItem icon="settings" intent="none" text="Default Action" />
        </Menu>
      </Container>
    </Box>
  );
};

export const DisabledStates = () => {
  return (
    <Box flex={{direction: 'column', gap: 8}} padding={8}>
      <Container style={{width: '220px'}}>
        <Menu>
          <MenuItem
            icon="download_for_offline"
            text="Save (enabled)"
            onClick={() => alert('Saved!')} // eslint-disable-line no-alert
          />
          <MenuItem icon="download_for_offline" text="Save (disabled)" disabled />
          <Tooltip content="You don't have permission to delete" placement="left">
            <MenuItem icon="delete" intent="danger" text="Delete (disabled)" disabled />
          </Tooltip>
          <MenuItem icon="download" text="Download (enabled)" />
        </Menu>
      </Container>
    </Box>
  );
};

export const ActiveState = () => {
  return (
    <Box flex={{direction: 'column', gap: 8}} padding={8}>
      <Container style={{width: '200px'}}>
        <Menu>
          <MenuItem icon="check_circle" text="Selected Item" active />
          <MenuItem icon="settings" text="Normal Item" />
          <MenuItem icon="info" text="Another Item" />
        </Menu>
      </Container>
    </Box>
  );
};

export const WithLabels = () => {
  return (
    <Box flex={{direction: 'column', gap: 8}} padding={8}>
      <Container style={{width: '250px'}}>
        <Menu>
          <MenuItem icon="download_for_offline" text="Save" right="⌘S" />
          <MenuItem icon="content_copy" text="Copy" right="⌘C" />
          <MenuItem icon="copy_to_clipboard" text="Paste" right="⌘V" />
          <MenuDivider />
          <MenuItem icon="search" text="Find" right="⌘F" />
          <MenuItem icon="refresh" text="Reload" right="⌘R" />
        </Menu>
      </Container>
    </Box>
  );
};

export const ExternalLinks = () => {
  return (
    <Box flex={{direction: 'column', gap: 8}} padding={8}>
      <Container style={{width: '250px'}}>
        <Menu>
          <MenuExternalLink
            icon="open_in_new"
            text="Open Documentation"
            href="https://docs.dagster.io"
          />
          <MenuExternalLink icon="github" text="View on GitHub" href="https://github.com" />
          <MenuDivider />
          <MenuItem icon="info" text="About" />
        </Menu>
      </Container>
    </Box>
  );
};

export const ComplexContent = () => {
  const [checkedItems, setCheckedItems] = useState<Set<string>>(() => new Set());
  const onChange = useCallback((item: string, checked: boolean) => {
    setCheckedItems((current) => {
      const copy = new Set(current);
      if (checked) {
        copy.add(item);
      } else {
        copy.delete(item);
      }
      return copy;
    });
  }, []);

  return (
    <Box flex={{direction: 'column', gap: 8}} padding={8}>
      <Container style={{width: '280px'}}>
        <Menu>
          <MenuItemForInteractiveContent>
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <Checkbox
                checked={checkedItems.has('completed')}
                label="Show completed items"
                onChange={(e) => onChange('completed', e.target.checked)}
                style={{width: '100%'}}
              />
            </Box>
          </MenuItemForInteractiveContent>
          <MenuItemForInteractiveContent>
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <Checkbox
                checked={checkedItems.has('archived')}
                label="Show archived items"
                onChange={(e) => onChange('archived', e.target.checked)}
              />
            </Box>
          </MenuItemForInteractiveContent>
          <MenuDivider />
          <MenuItem
            icon={<Spinner purpose="body-text" />}
            text={
              <Box flex={{direction: 'row', gap: 4}}>
                <span>Loading latest data...</span>
              </Box>
            }
            disabled
          />
        </Menu>
      </Container>
    </Box>
  );
};

export const ButtonsAndLinks = () => {
  return (
    <Box flex={{direction: 'column', gap: 8}} padding={8}>
      <Container style={{width: '250px'}}>
        <Menu>
          <MenuExternalLink
            icon="link"
            text="External link"
            href="https://example.com"
            onClick={() => alert('Link clicked!')} // eslint-disable-line no-alert
          />
          <MenuItem
            icon="toggle_on"
            text="Button (MenuItem)"
            onClick={() => alert('Button clicked!')} // eslint-disable-line no-alert
          />
          <MenuItem text="Disabled item" icon="info" disabled />
        </Menu>
      </Container>
    </Box>
  );
};

export const InteractiveMenu = () => {
  return (
    <Box flex={{direction: 'column', gap: 8}} padding={8}>
      <Container style={{width: '220px'}}>
        <Menu>
          {/* eslint-disable-next-line no-alert */}
          <MenuItem icon="execute" text="Run Job" onClick={() => alert('Running job...')} />
          {/* eslint-disable-next-line no-alert */}
          <MenuItem icon="pause" text="Pause Job" onClick={() => alert('Pausing job...')} />
          <MenuItem
            icon="cancel"
            intent="danger"
            text="Stop Job"
            onClick={() => alert('Stopped!')} // eslint-disable-line no-alert
          />
          <MenuDivider />
          {/* eslint-disable-next-line no-alert */}
          <MenuItem icon="settings" text="Configure" onClick={() => alert('Opening settings...')} />
        </Menu>
      </Container>
    </Box>
  );
};

const Container = styled.div`
  box-shadow: ${Colors.shadowDefault()} 0px 2px 12px;
`;
