"""Reading .pypirc file.

Lifted wholesale from (MIT-licensed)
https://pypi-uploader.readthedocs.io/en/latest/_modules/pypiuploader/pypirc.html,
https://pypi.org/project/pypi-uploader/.
"""

try:
    import configparser
except ImportError:  # pragma: no cover
    import ConfigParser as configparser
import os


class ConfigFileError(Exception):

    """Raised when a PyPI config file does not exist."""


class RCParser(object):

    """Parser for the ``~/.pypirc`` file.

    Parses the file to find a specified repository's config:

    * repository URL
    * username
    * password

    Example:

    >>> parser = RCParser.from_file()
    >>> parser.get_repository_config('internal')
    {'repository': 'http://localhost/', 'username': 'foo', 'password': 'bar'}

    :param config_parser:
        :class:`configparser.ConfigParser` instance with the ``.pypirc``
        content loaded.

    """

    CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".pypirc")

    def __init__(self, config_parser):
        #: :class:`configparser.ConfigParser` instance to parse.
        self.config = config_parser

    @classmethod
    def from_file(cls, path=None):
        """Read a config file and instantiate the RCParser.

        Create new :class:`configparser.ConfigParser` for the given **path**
        and instantiate the :class:`RCParser` with the ConfigParser as
        :attr:`config` attribute.

        If the **path** doesn't exist, raise :exc:`ConfigFileError`.
        Otherwise return a new :class:`RCParser` instance.

        :param path:
            Optional path to the config file to parse.
            If not given, use ``'~/.pypirc'``.

        """
        path = path or cls.CONFIG_PATH
        if not os.path.exists(path):
            error = "Config file not found: {0!r}".format(path)
            raise ConfigFileError(error)
        config = read_config(path)
        return cls(config)

    def get_repository_config(self, repository):
        """Get config dictionary for the given repository.

        If the repository section is not found in the config file,
        return ``None``.  If the file is invalid, raise
        :exc:`configparser.Error`.

        Otherwise return a dictionary with:

        * ``'repository'`` -- the repository URL
        * ``'username'`` -- username for authentication
        * ``'password'`` -- password for authentication

        :param repository:
            Name or URL of the repository to find in the ``.pypirc`` file.
            The repository section must be defined in the config file.

        """
        servers = self._read_index_servers()
        repo_config = self._find_repo_config(servers, repository)
        return repo_config

    def _read_index_servers(self):
        try:
            servers_string = self.config.get("distutils", "index-servers")
        except configparser.NoSectionError:
            return
        for server in servers_string.split("\n"):
            server = server.strip()
            if server and server != "pypi":
                yield server

    def _find_repo_config(self, servers, repository):
        for server in servers:
            server_repository = self.config.get(server, "repository")
            if repository in (server, server_repository):
                username, password = self._read_server_auth(server)
                return {"repository": server_repository, "username": username, "password": password}
        return None

    def _read_server_auth(self, server_name):
        username = self.config.get(server_name, "username")
        try:
            password = self.config.get(server_name, "password")
        except configparser.NoOptionError:
            password = None
        return username, password


def read_config(path):
    """Make a config parser for the given config file.

    Return a :class:`configparser.ConfigParser` instance with the given file
    loaded.

    :param path:
        Path to the config file to read.

    """
    config = configparser.ConfigParser()
    config.read(path)
    return config
