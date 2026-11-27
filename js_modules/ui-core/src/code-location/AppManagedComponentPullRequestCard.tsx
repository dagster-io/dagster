import {Box, Colors, Icon, Text} from '@dagster-io/ui-components';

interface Props {
  pullRequestUrl: string;
  branchName: string;
  pullRequestNumber: number;
}

/**
 * Shown after the git-backed authoring submit opens a pull request: links to the
 * PR and names the branch it was opened from. The change reaches production when
 * the PR is merged.
 */
export const AppManagedComponentPullRequestCard = ({
  pullRequestUrl,
  branchName,
  pullRequestNumber,
}: Props) => (
  <Box
    flex={{direction: 'column', gap: 12}}
    padding={{vertical: 16, horizontal: 20}}
    border="all"
    style={{borderRadius: 8}}
  >
    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
      <Icon name="git_pr" color={Colors.accentGreen()} />
      <Text size={16} weight={600}>
        Pull request opened
      </Text>
    </Box>
    <Text size={14} color="textLight">
      Review and merge the pull request to apply this change to production.
    </Text>
    <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
      <a href={pullRequestUrl} target="_blank" rel="noreferrer">
        {branchName} (#{pullRequestNumber})
      </a>
      <Icon name="open_in_new" color={Colors.linkDefault()} />
    </Box>
  </Box>
);
