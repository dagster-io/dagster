import {Box, Heading, Text} from '@dagster-io/ui-components';

export const isEmptyChildren = (children: React.ReactNode) =>
  !children || (children instanceof Array && children.length === 0);

export const AttributeAndValue = ({
  label,
  children,
}: {
  label: React.ReactNode;
  children: React.ReactNode;
}) => {
  if (isEmptyChildren(children)) {
    return null;
  }

  return (
    <Box flex={{direction: 'column', gap: 6, alignItems: 'stretch'}}>
      <Heading size={14} weight={600}>
        {label}
      </Heading>
      <Text size={14} style={{maxWidth: '100%'}}>
        <Box flex={{gap: 4, wrap: 'wrap'}}>{children}</Box>
      </Text>
    </Box>
  );
};

export const NoValue = () => (
  <Text size={14} color="textLighter">
    –
  </Text>
);
