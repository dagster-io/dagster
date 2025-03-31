import {
  Box,
  Button,
  Dialog,
  DialogBody,
  DialogFooter,
  Group,
  Icon,
  TextInput,
  Tooltip,
} from '@dagster-io/ui-components';
import {Dispatch, SetStateAction, useEffect, useState} from 'react';
import styled from 'styled-components';

import {PipelineRunTag} from '../app/ExecutionSessionStorage';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {ExecutionTag} from '../graphql/types';
import {RunTag} from '../runs/RunTag';
import {useCopyAction} from '../runs/RunTags';
import {TagAction} from '../ui/TagActions';

interface ITagEditorProps {
  tagsFromDefinition?: PipelineRunTag[];
  tagsFromSession: PipelineRunTag[];
  open: boolean;
  onChange: (tags: PipelineRunTag[]) => void;
  onRequestClose: () => void;
}

interface ITagContainerProps {
  tagsFromDefinition?: PipelineRunTag[];
  tagsFromSession: PipelineRunTag[];
  onRequestEdit: () => void;
  actions?: TagAction[];
}

export const TagEditor = ({
  tagsFromDefinition = [],
  tagsFromSession = [],
  open,
  onChange,
  onRequestClose,
}: ITagEditorProps) => {
  const [editState, setEditState] = useState(() =>
    tagsFromSession.length ? tagsFromSession : [{key: '', value: ''}],
  );

  // Reset the edit state when you close and re-open the modal, or when
  // tagsFromSession change while the modal is closed.
  useEffect(() => {
    if (!open) {
      setEditState(tagsFromSession.length ? tagsFromSession : [{key: '', value: ''}]);
    }
  }, [tagsFromSession, open]);

  const {toError, toSave} = validateTagEditState(editState);

  const onSave = () => {
    if (!toError.length) {
      onChange(toSave);
      onRequestClose();
    }
  };

  const disabled = editState === tagsFromSession || !!toError.length;

  return (
    <Dialog
      icon="info"
      onClose={onRequestClose}
      style={{minWidth: 700}}
      title="Add tags to run"
      isOpen={open}
    >
      <DialogBody>
        <EditableTagList
          editState={editState}
          editableTagsHeading="Custom tags:"
          setEditState={setEditState}
          tagsFromDefinition={tagsFromDefinition}
        />
      </DialogBody>
      <DialogFooter>
        <Button onClick={onRequestClose}>Cancel</Button>
        <ShortcutHandler
          shortcutLabel="⌥Enter"
          shortcutFilter={(e) => e.code === 'Enter' && e.altKey}
          onShortcut={onSave}
        >
          <Button intent="primary" onClick={onSave} disabled={disabled}>
            Apply
          </Button>
        </ShortcutHandler>
      </DialogFooter>
    </Dialog>
  );
};

export function validateTagEditState(editState: ExecutionTag[]) {
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

  return {toSave, toError};
}

export const EditableTagList = ({
  editState,
  editableTagsHeading,
  setEditState,
  tagsFromDefinition = [],
  tagsFromParentRun = [],
}: {
  editState: ExecutionTag[];
  editableTagsHeading?: string;
  setEditState: Dispatch<SetStateAction<PipelineRunTag[]>>;
  tagsFromDefinition?: PipelineRunTag[];
  tagsFromParentRun?: ExecutionTag[];
}) => {
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

  const copyAction = useCopyAction();

  return (
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
              return <RunTag tag={tag} key={key} actions={[copyAction]} />;
            })}
          </TagList>
        </Group>
      ) : null}
      <Box flex={{direction: 'column', gap: 12}}>
        {editableTagsHeading ? <div>{editableTagsHeading}</div> : null}
        <Box flex={{direction: 'column', gap: 8}}>
          {editState.map((tag, idx) => {
            const {key, value} = tag;
            const parent = tagsFromParentRun.find((t) => t.key === key);
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
                  readOnly={!!parent}
                  onChange={(e) => onTagEdit(e.target.value, value, idx)}
                />
                <TextInput
                  placeholder="Tag Value"
                  value={value}
                  onChange={(e) => onTagEdit(key, e.target.value, idx)}
                />
                {!parent && (
                  <Button
                    disabled={editState.length === 1 && !key.trim() && !value.trim()}
                    onClick={() => onRemove(idx)}
                    icon={<Icon name="delete" />}
                  >
                    Remove
                  </Button>
                )}
              </div>
            );
          })}
        </Box>
        <Box margin={{left: 2}} flex={{direction: 'row'}}>
          <Button onClick={addTagEntry} icon={<Icon name="add_circle" />}>
            Add custom tag
          </Button>
        </Box>
      </Box>
    </Group>
  );
};

export const TagContainer = ({
  tagsFromSession,
  tagsFromDefinition,
  actions,
}: ITagContainerProps) => {
  return (
    <Container>
      <TagList>
        {tagsFromDefinition
          ? tagsFromDefinition.map((tag, idx) => {
              const {key} = tag;
              const anyOverride = tagsFromSession.some((sessionTag) => sessionTag.key === key);
              if (anyOverride) {
                return (
                  <Tooltip key={key} content="Overriden by custom tag value" placement="top">
                    <span style={{opacity: 0.2}}>
                      <RunTag tag={tag} key={idx} actions={actions} />
                    </span>
                  </Tooltip>
                );
              }
              return <RunTag tag={tag} key={idx} actions={actions} />;
            })
          : undefined}
        {tagsFromSession.map((tag, idx) => (
          <RunTag tag={tag} key={idx} actions={actions} />
        ))}
      </TagList>
    </Container>
  );
};

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
