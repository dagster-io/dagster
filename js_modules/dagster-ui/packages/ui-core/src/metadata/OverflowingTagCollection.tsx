import {
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Tag,
} from '@dagster-io/ui-components';
import {useEffect, useRef, useState} from 'react';
import styled from 'styled-components';

import {DefinitionTag} from '../graphql/types';
import {RunTags} from '../runs/RunTags';
import {buildTagString} from '../ui/tagAsString';

const SHOW_EXTRA_TAGS_WIDTH = 20;

const getOverflowingTag = (target: HTMLDivElement | null) => {
  if (!target || target.offsetWidth >= target.scrollWidth) {
    return false;
  }
  // find the first tag that is overflowing
  for (let i = 0; i < target.children.length; i++) {
    const child = target.children[i];
    if (
      child &&
      child?.getBoundingClientRect()?.right >
        target.getBoundingClientRect().right - SHOW_EXTRA_TAGS_WIDTH
    ) {
      console.log(
        child,
        child?.getBoundingClientRect()?.right,
        target.getBoundingClientRect().right,
      );
      return i;
    }
  }
  return target.children.length;
};

type OverflowingTagCollectionProps = {
  tags: DefinitionTag[];
};

export const OverflowingTagCollection = ({tags}: OverflowingTagCollectionProps) => {
  const [showColumnTags, setShowColumnTags] = useState(false);
  const [overflowing, setOverflowing] = useState<number | false>(false);
  const container = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const tag = getOverflowingTag(container.current);
    if (tag) {
      setOverflowing(tag);
    }
  }, [overflowing]);

  const tagsToRender = overflowing !== false ? tags.slice(0, overflowing) : tags;
  const hiddenTagNumber = tags.length - tagsToRender.length;

  const openColumnTagDialog = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setShowColumnTags(true);
  };

  return (
    <div
      ref={container}
      style={{
        display: 'flex',
        gap: 4,
        flexWrap: 'nowrap',
        overflow: overflowing !== false ? 'visible' : 'hidden',
        // backgroundColor: overflowing ? 'red' : 'blue',
      }}
      className="columnTags"
    >
      {tagsToRender.map((tag) => (
        <Tag key={tag.key}>
          <TagCollectionLabel
            style={{
              textOverflow: 'ellipsis',
              overflowX: 'hidden',
              maxWidth: overflowing !== false ? '70px' : undefined,
              paddingRight: '20',
              verticalAlign: 'top',
              cursor: overflowing ? 'pointer' : 'default',
            }}
            onClick={overflowing ? openColumnTagDialog : undefined}
          >
            {buildTagString(tag)}
          </TagCollectionLabel>
        </Tag>
      ))}
      {overflowing !== false && (
        <ButtonLink
          color={Colors.textLight()}
          style={{margin: '-4px', padding: '4px', cursor: 'pointer'}}
          onClick={openColumnTagDialog}
        >
          <TagCollectionLabel className="hiddenTagNumber">+{hiddenTagNumber}</TagCollectionLabel>
        </ButtonLink>
      )}
      <Dialog
        isOpen={showColumnTags}
        title="Tags"
        canOutsideClickClose
        canEscapeKeyClose
        onClose={() => {
          setShowColumnTags(false);
        }}
      >
        <DialogBody>
          <RunTags tags={tags} />
        </DialogBody>
        <DialogFooter topBorder>
          <Button
            intent="primary"
            onClick={() => {
              setShowColumnTags(false);
            }}
          >
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
};

// This is a p so that we can use it in the lineage view & have it nested in an anchor tag but not
// have it underlined - only certain tag types can do this
const TagCollectionLabel = styled.p`
  margin: 0;
  padding: 0;
`;
