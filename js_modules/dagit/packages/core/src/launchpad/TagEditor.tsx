import * as React from 'react';
import styled from 'styled-components/macro';

import {PipelineRunTag} from '../app/LocalStorage';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {RunTag} from '../runs/RunTag';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {ColorsWIP} from '../ui/Colors';
import {DialogBody, DialogFooter, DialogWIP} from '../ui/Dialog';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {TextInput} from '../ui/TextInput';
import {Tooltip} from '../ui/Tooltip';

interface ITagEditorProps {
  tagsFromDefinition?: PipelineRunTag[];
  tagsFromSession: PipelineRunTag[];
  open: boolean;
  onChange: (tags: PipelineRunTag[]) => void;
  onRequestClose: () => void;
}

interface ITagContainerProps {
  tags: {
    fromDefinition?: PipelineRunTag[];
    fromSession?: PipelineRunTag[];
  };
  onRequestEdit: () => void;
}

export const TagEditor: React.FC<ITagEditorProps> = ({
  tagsFromDefinition = [],
  tagsFromSession = [],
  open,
  onChange,
  onRequestClose,
}) => {
  const [editState, setEditState] = React.useState(() =>
    tagsFromSession.length ? tagsFromSession : [{key: '', value: ''}],
  );

  const toSave: PipelineRunTag[] = editState
    .map((tag: PipelineRunTag) => ({
      key: tag.key.trim(),
      value: tag.value.trim(),
    }))
    .filter((tag) => tag.key && tag.value);
  const toError = editState
    .map((tag: PipelineRunTag) => ({
      key: tag.key.trim(),
      value: tag.value.trim(),
    }))
    .filter((tag) => !tag.key !== !tag.value);

  const onSave = () => {
    if (!toError.length) {
      onChange(toSave);
      onRequestClose();
    }
  };

  const disabled = editState === tagsFromSession || !!toError.length;

  const onTagEdit = (key: string, value: string, idx: number) => {
    setEditState((current) => [...current.slice(0, idx), {key, value}, ...current.slice(idx + 1)]);
  };

  const onRemove = (idx: number) => {
    setEditState((current) => {
      if (idx === 0 && current.length === 1) {
        // If we're deleting the only item, just wipe it out.
        return [{key: '', value: ''}];
      }
      return [...current.slice(0, idx), ...current.slice(idx + 1)];
    });
  };

  const addTagEntry = () => {
    setEditState((current) => [...current, {key: '', value: ''}]);
  };

  return (
    <DialogWIP
      icon="info"
      onClose={onRequestClose}
      style={{minWidth: 700}}
      title="Add tags to run"
      isOpen={open}
    >
      <DialogBody>
        <Group spacing={16} direction="column">
          {tagsFromDefinition.length ? (
            <Group direction="column" spacing={8}>
              <Box margin={{left: 2}} style={{fontSize: '13px', fontWeight: 500}}>
                Tags from definition:
              </Box>
              <TagList>
                {tagsFromDefinition.map((tag, idx) => {
                  const {key} = tag;
                  const anyOverride = editState.some((editable) => editable.key === key);
                  if (anyOverride) {
                    return (
                      <Tooltip key={key} content="Overriden by custom tag value" placement="top">
                        <span style={{opacity: 0.2}}>
                          <RunTag tag={tag} key={idx} />
                        </span>
                      </Tooltip>
                    );
                  }
                  return <RunTag tag={tag} key={key} />;
                })}
              </TagList>
            </Group>
          ) : null}
          <Box flex={{direction: 'column', gap: 12}}>
            <div>Custom tags:</div>
            <Box flex={{direction: 'column', gap: 8}}>
              {editState.map((tag, idx) => {
                const {key, value} = tag;
                return (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      flexDirection: 'row',
                      gap: 8,
                    }}
                  >
                    <TextInput
                      placeholder="Tag Key"
                      value={key}
                      onChange={(e) => onTagEdit(e.target.value, value, idx)}
                    />
                    <TextInput
                      placeholder="Tag Value"
                      value={value}
                      onChange={(e) => onTagEdit(key, e.target.value, idx)}
                    />
                    <ButtonWIP
                      disabled={editState.length === 1 && !key.trim() && !value.trim()}
                      onClick={() => onRemove(idx)}
                      icon={<IconWIP name="delete" />}
                    >
                      Remove
                    </ButtonWIP>
                  </div>
                );
              })}
            </Box>
            <Box margin={{left: 2}} flex={{direction: 'row'}}>
              <ButtonWIP onClick={addTagEntry} icon={<IconWIP name="add_circle" />}>
                Add custom tag
              </ButtonWIP>
            </Box>
          </Box>
        </Group>
      </DialogBody>
      <DialogFooter>
        <ButtonWIP onClick={onRequestClose}>Cancel</ButtonWIP>
        <ShortcutHandler
          shortcutLabel="⌥Enter"
          shortcutFilter={(e) => e.keyCode === 13 && e.altKey}
          onShortcut={onSave}
        >
          <ButtonWIP intent="primary" onClick={onSave} disabled={disabled}>
            Apply
          </ButtonWIP>
        </ShortcutHandler>
      </DialogFooter>
    </DialogWIP>
  );
};

export const TagContainer = ({tags, onRequestEdit}: ITagContainerProps) => {
  const {fromDefinition = [], fromSession = []} = tags;
  return (
    <Container>
      <TagList>
        {fromDefinition.map((tag, idx) => {
          const {key} = tag;
          const anyOverride = fromSession.some((sessionTag) => sessionTag.key === key);
          if (anyOverride) {
            return (
              <Tooltip key={key} content="Overriden by custom tag value" placement="top">
                <span style={{opacity: 0.2}}>
                  <RunTag tag={tag} key={idx} />
                </span>
              </Tooltip>
            );
          }
          return <RunTag tag={tag} key={idx} />;
        })}
        {fromSession.map((tag, idx) => (
          <RunTag tag={tag} key={idx} />
        ))}
      </TagList>
      <TagEditorLink onRequestOpen={onRequestEdit}>
        <Group direction="row" spacing={4} alignItems="center">
          <IconWIP name="edit" color={ColorsWIP.Gray500} /> Edit Tags
        </Group>
      </TagEditorLink>
    </Container>
  );
};

interface ITagEditorLinkProps {
  onRequestOpen: () => void;
  children: React.ReactNode;
}

const TagEditorLink = ({onRequestOpen, children}: ITagEditorLinkProps) => (
  <ShortcutHandler
    shortcutLabel="⌥T"
    shortcutFilter={(e) => e.keyCode === 84 && e.altKey}
    onShortcut={onRequestOpen}
  >
    <Link onClick={onRequestOpen}>{children}</Link>
  </ShortcutHandler>
);

const Container = styled.div`
  align-items: flex-start;
  display: flex;
  flex-direction: row;
`;
const TagList = styled.div`
  display: flex;
  flex: 1;
  flex-wrap: wrap;
  gap: 4px;
`;
const Link = styled.div`
  color: #666;
  cursor: pointer;
  margin: 4px 12px;
  font-size: 12px;
  &:hover {
    color: #aaa;
  }
`;
