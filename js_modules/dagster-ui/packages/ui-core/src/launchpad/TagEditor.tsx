import {
  Box,
  Button,
  Dialog,
  DialogBody,
  DialogFooter,
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
      title="为运行添加标签"
      isOpen={open}
    >
      <DialogBody>
        <EditableTagList
          editState={editState}
          editableTagsHeading="自定义标签:"
          setEditState={setEditState}
          tagsFromDefinition={tagsFromDefinition}
        />
      </DialogBody>
      <DialogFooter>
        <Button onClick={onRequestClose}>取消</Button>
        <ShortcutHandler
          shortcutLabel="⌥Enter"
          shortcutFilter={(e) => e.code === 'Enter' && e.altKey}
          onShortcut={onSave}
        >
          <Button intent="primary" onClick={onSave} disabled={disabled}>
            应用
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
    <Box flex={{direction: 'column', gap: 16}}>
      {tagsFromDefinition.length ? (
        <Box flex={{direction: 'column', gap: 8}}>
          <Box margin={{left: 2}} style={{fontSize: '13px', fontWeight: 500}}>
            定义中的标签:
          </Box>
          <TagList>
            {tagsFromDefinition.map((tag, idx) => {
              const {key} = tag;
              const anyOverride = editState.some((editable) => editable.key === key);
              if (anyOverride) {
                return (
                  <Tooltip key={key} content="已被自定义标签值覆盖" placement="top">
                    <span style={{opacity: 0.2}}>
                      <RunTag tag={tag} key={idx} />
                    </span>
                  </Tooltip>
                );
              }
              return <RunTag tag={tag} key={key} actions={[copyAction]} />;
            })}
          </TagList>
        </Box>
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
                  placeholder="标签键"
                  value={key}
                  readOnly={!!parent}
                  onChange={(e) => onTagEdit(e.target.value, value, idx)}
                />
                <TextInput
                  placeholder="标签值"
                  value={value}
                  onChange={(e) => onTagEdit(key, e.target.value, idx)}
                />
                {!parent && (
                  <Button
                    disabled={editState.length === 1 && !key.trim() && !value.trim()}
                    onClick={() => onRemove(idx)}
                    icon={<Icon name="delete" />}
                  >
                    移除
                  </Button>
                )}
              </div>
            );
          })}
        </Box>
        <Box margin={{left: 2}} flex={{direction: 'row'}}>
          <Button onClick={addTagEntry} icon={<Icon name="add_circle" />}>
            添加自定义标签
          </Button>
        </Box>
      </Box>
    </Box>
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
                  <Tooltip key={key} content="已被自定义标签值覆盖" placement="top">
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
