import {
  BaseTag,
  Box,
  Colors,
  Icon,
  MenuItem,
  MiddleTruncate,
  TagSelectorContainer,
  TagSelectorDefaultTagTooltipStyle,
  TagSelectorWithSearch,
} from '@dagster-io/ui-components';
import styled from 'styled-components';

interface Props {
  allPartitions: string[];
  selectedPartition: string | null;
  selectPartition: (partition: string | null) => void;
}

export const PartitionTagSelector = ({
  allPartitions,
  selectedPartition,
  selectPartition,
}: Props) => {
  return (
    <TagSelectorWrapper>
      <TagSelectorWithSearch
        closeOnSelect
        placeholder="Select a partition to view its result"
        allTags={allPartitions}
        selectedTags={selectedPartition ? [selectedPartition] : []}
        setSelectedTags={(tags) => {
          selectPartition(tags[tags.length - 1] || null);
        }}
        renderDropdownItem={(tag, props) => <MenuItem text={tag} onClick={props.toggle} />}
        renderDropdown={(dropdown) => (
          <Box padding={{top: 8, horizontal: 4}} style={{width: '370px'}}>
            {dropdown}
          </Box>
        )}
        renderTag={(tag, tagProps) => (
          <BaseTag
            key={tag}
            textColor={Colors.textLight()}
            fillColor={Colors.backgroundGray()}
            icon={<Icon name="partition" color={Colors.accentGray()} />}
            label={
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr auto',
                  gap: 4,
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  maxWidth: '120px',
                }}
                data-tooltip={tag}
                data-tooltip-style={TagSelectorDefaultTagTooltipStyle}
              >
                <MiddleTruncate text={tag} />
                <Box style={{cursor: 'pointer'}} onClick={tagProps.remove}>
                  <Icon name="close" />
                </Box>
              </div>
            }
          />
        )}
        usePortal={false}
      />
      <SearchIconWrapper>
        <Icon name="search" />
      </SearchIconWrapper>
    </TagSelectorWrapper>
  );
};

const TagSelectorWrapper = styled.div`
  position: relative;

  ${TagSelectorContainer} {
    width: 370px;
    padding-left: 32px;
    height: 36px;
  }
`;

const SearchIconWrapper = styled.div`
  position: absolute;
  left: 12px;
  top: 0px;
  bottom: 0px;
  pointer-events: none;
  display: flex;
  align-items: center;
`;
