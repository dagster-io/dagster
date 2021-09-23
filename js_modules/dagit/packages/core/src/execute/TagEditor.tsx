import {Button, Classes, Dialog} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import styled from 'styled-components/macro';

import {PipelineRunTag} from '../app/LocalStorage';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {RunTag} from '../runs/RunTag';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';

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
    setEditState((current) => [...current.slice(0, idx), ...current.slice(idx + 1)]);
  };

  const addTagEntry = () => {
    setEditState((current) => [...current, {key: '', value: ''}]);
  };

  return (
    <Dialog
      icon="info-sign"
      onClose={onRequestClose}
      style={{minWidth: 500}}
      title="Add tags to run"
      usePortal={true}
      isOpen={open}
    >
      <div
        className={Classes.DIALOG_BODY}
        style={{
          margin: 0,
          marginBottom: 17,
          height: `calc(100% - 85px)`,
          position: 'relative',
        }}
      >
        <Group padding={16} spacing={16} direction="column">
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
          <Group direction="column" spacing={8}>
            <Box margin={{left: 2}} style={{fontSize: '13px', fontWeight: 500}}>
              Custom tags:
            </Box>
            <div>
              {editState.map((tag, idx) => {
                const {key, value} = tag;
                return (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      flexDirection: 'row',
                      marginBottom: 8,
                    }}
                  >
                    <Input
                      type="text"
                      placeholder="Tag Key"
                      value={key}
                      onChange={(e) => onTagEdit(e.target.value, value, idx)}
                    />
                    <Input
                      type="text"
                      placeholder="Tag Value"
                      value={value}
                      onChange={(e) => onTagEdit(key, e.target.value, idx)}
                    />
                    <RemoveButton onClick={() => onRemove(idx)}>
                      <IconWIP name="close" />
                    </RemoveButton>
                  </div>
                );
              })}
              <Box margin={{left: 2}}>
                <ButtonLink onClick={addTagEntry}>+ Add custom tag</ButtonLink>
              </Box>
            </div>
          </Group>
        </Group>
      </div>
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <Button onClick={onRequestClose}>Cancel</Button>
          <ShortcutHandler
            shortcutLabel="⌥Enter"
            shortcutFilter={(e) => e.keyCode === 13 && e.altKey}
            onShortcut={onSave}
          >
            <Button intent="primary" onClick={onSave} disabled={disabled}>
              Apply
            </Button>
          </ShortcutHandler>
        </div>
      </div>
    </Dialog>
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
    shortcutLabel={'⌥T'}
    shortcutFilter={(e) => e.keyCode === 84 && e.altKey}
    onShortcut={onRequestOpen}
  >
    <Link onClick={onRequestOpen}>{children}</Link>
  </ShortcutHandler>
);

const RemoveButton = styled.button`
  background: none;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  padding: 0 3px;

  :hover {
    background-color: ${ColorsWIP.Gray200};
  }
`;

const Input = styled.input`
  flex: 1;
  margin-right: 10px;
  border-radius: 3px;
  font-size: 14px;
  padding: 3px 7px;
  border: 1px solid #cccccc;
`;
const Container = styled.div`
  align-items: flex-start;
  display: flex;
  flex-direction: row;
  border-bottom: 1px solid #ececec;
  padding: 4px 8px;
`;
const TagList = styled.div`
  display: flex;
  flex: 1;
  flex-wrap: wrap;
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
