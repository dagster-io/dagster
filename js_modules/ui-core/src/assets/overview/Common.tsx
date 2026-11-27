import {Box, Colors, Heading, Skeleton, Text} from '@dagster-io/ui-components';

export const SectionSkeleton = () => (
  <Box flex={{direction: 'column', gap: 6}} style={{width: '100%'}}>
    <Skeleton $height={16} $width="90%" />
    <Skeleton $height={16} />
    <Skeleton $height={16} $width="60%" />
  </Box>
);

export const SectionEmptyState = ({
  title,
  description,
  learnMoreLink,
  interaction,
}: {
  title: string;
  description: string;
  learnMoreLink: string;
  interaction?: React.ReactNode;
}) => (
  <Box
    padding={24}
    style={{background: Colors.backgroundLight(), borderRadius: 8}}
    flex={{direction: 'column', gap: 8}}
  >
    <Heading size={14} weight={600}>
      {title}
    </Heading>
    <Text size={14}>{description}</Text>
    {learnMoreLink ? (
      <a href={learnMoreLink} target="_blank" rel="noreferrer">
        Learn more
      </a>
    ) : undefined}
    {interaction}
  </Box>
);
