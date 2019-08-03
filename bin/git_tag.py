import re
import subprocess


def get_git_tag():
    try:
        git_tag = str(
            subprocess.check_output(
                ['git', 'describe', '--exact-match', '--abbrev=0'], stderr=subprocess.STDOUT
            )
        ).strip('\'b\\n')
    except subprocess.CalledProcessError as exc_info:
        match = re.search(
            'fatal: no tag exactly matches \'(?P<commit>[a-z0-9]+)\'', str(exc_info.output)
        )
        if match:
            raise Exception(
                'Bailing: there is no git tag for the current commit, {commit}'.format(
                    commit=match.group('commit')
                )
            )
        raise Exception(str(exc_info.output))

    return git_tag


def get_most_recent_git_tag():
    try:
        git_tag = str(
            subprocess.check_output(['git', 'describe', '--abbrev=0'], stderr=subprocess.STDOUT)
        ).strip('\'b\\n')
    except subprocess.CalledProcessError as exc_info:
        raise Exception(str(exc_info.output))
    return git_tag


def set_git_tag(tag, signed=False):
    try:
        if signed:
            subprocess.check_output(['git', 'tag', '-s', '-m', tag, tag], stderr=subprocess.STDOUT)
        else:
            subprocess.check_output(['git', 'tag', '-a', '-m', tag, tag], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc_info:
        match = re.search('error: gpg failed to sign the data', str(exc_info.output))
        if match:
            raise Exception(
                'Bailing: cannot sign tag. You may find '
                'https://stackoverflow.com/q/39494631/324449 helpful. Original error '
                'output:\n{output}'.format(output=str(exc_info.output))
            )

        match = re.search(
            r'fatal: tag \'(?P<tag>[\.a-z0-9]+)\' already exists', str(exc_info.output)
        )
        if match:
            raise Exception(
                'Bailing: cannot release version tag {tag}: already exists'.format(
                    tag=match.group('tag')
                )
            )
        raise Exception(str(exc_info.output))

    return tag
