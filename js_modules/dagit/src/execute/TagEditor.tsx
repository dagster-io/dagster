import * as React from 'react';
import {Button, Classes, Dialog, Icon} from '@blueprintjs/core';
import styled from 'styled-components/macro';
import {ShortcutHandler} from '../ShortcutHandler';
import {RunTag} from '../runs/RunTag';
import {IconNames} from '@blueprintjs/icons';
import {PipelineRunTag} from '../LocalStorage';

interface ITagEditorProps {
  tags: PipelineRunTag[];
  open: boolean;
  onChange: (tags: PipelineRunTag[]) => void;
  onRequestClose: () => void;
}
interface ITagContainerProps {
  tags: PipelineRunTag[];
  onRequestEdit: () => void;
}

export const TagEditor = ({tags: propTags, open, onChange, onRequestClose}: ITagEditorProps) => {
  const [tags, setTags] = React.useState(propTags.length ? propTags : [{key: '', value: ''}]);
  React.useEffect(() => {
    setTags(propTags.length ? propTags : [{key: '', value: ''}]);
  }, [propTags]);

  const toSave: PipelineRunTag[] = tags
    .map((tag: PipelineRunTag) => ({
      key: tag.key.trim(),
      value: tag.value.trim(),
    }))
    .filter((tag) => tag.key && tag.value);
  const toError = tags
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

  const disabled = tags === propTags || !!toError.length;

  const onTagEdit = (key: string, value: string, idx: number) => {
    const newTags = [...tags.slice(0, idx), {key, value}, ...tags.slice(idx + 1)];
    setTags(newTags);
  };
  const onRemove = (idx: number) => {
    setTags([...tags.slice(0, idx), ...tags.slice(idx + 1)]);
  };
  const addTagEntry = () => {
    setTags([...tags, {key: '', value: ''}]);
  };
  return (
    <Dialog
      icon="info-sign"
      onClose={onRequestClose}
      style={{minWidth: 500}}
      title={'Add tags to pipeline run'}
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
        <Form>
          {tags.map((tag, idx) => {
            const {key, value} = tag;
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  flexDirection: 'row',
                  marginBottom: 10,
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
                <Remove onClick={() => onRemove(idx)} />
              </div>
            );
          })}
          <LinkButton onClick={addTagEntry}>+ Add another tag</LinkButton>
        </Form>
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
  return (
    <Container>
      {tags.map((tag, idx) => {
        return <RunTag tag={tag} key={idx} />;
      })}
      <TagEditorLink onRequestOpen={onRequestEdit}>
        <Icon icon={IconNames.EDIT} iconSize={12} style={{marginBottom: 2}} /> Edit Tags
      </TagEditorLink>
    </Container>
  );
};

interface ITagEditorLinkProps {
  onRequestOpen: () => void;
  children: React.ReactNode;
}

export const TagEditorLink = ({onRequestOpen, children}: ITagEditorLinkProps) => (
  <ShortcutHandler
    shortcutLabel={'⌥T'}
    shortcutFilter={(e) => e.keyCode === 84 && e.altKey}
    onShortcut={onRequestOpen}
  >
    <Link onClick={onRequestOpen}>{children}</Link>
  </ShortcutHandler>
);

const Remove = styled(Icon).attrs({icon: IconNames.CROSS})`
  align-self: center;
  color: #aaaaaa;
  cursor: pointer;
  border: 1px solid transparent;
  padding: 3px;
  &:hover {
    color: #999999;
    border: 1px solid #cccccc;
    border-radius: 1px;
  }
`;
const Form = styled.div`
  margin: 30px;
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
  display: flex;
  flex-direction: row;
  border-bottom: 1px solid #ececec;
  padding: 3px 7px;
`;
const Link = styled.div`
  align-self: center;
  color: #666;
  cursor: pointer;
  margin: 0 15px;
  font-size: 12px;
  &:hover {
    color: #aaa;
  }
`;
const LinkButton = styled.button`
  background: inherit;
  border: none;
  cursor: pointer;
  font-size: inherit;
  text-decoration: none;
  color: #106ba3;
  &:hover {
    text-decoration: underline;
  }
`;
