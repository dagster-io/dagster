import os
import sys
try:
    from graphql.execution.executors.asyncio import AsyncioExecutor as Executor
except ImportError:
    from graphql.execution.executors.thread import ThreadExecutor as Executor
from flask import Flask, send_file, send_from_directory
from flask_graphql import GraphQLView
from flask_cors import CORS

from dagster import check

from dagster.cli.dynamic_loader import (
    load_repository_object_from_target_info,
    DynamicObject,
)

from .schema import create_schema


class RepositoryContainer(object):
    '''
    This class solely exists to implement reloading semantics. We need to have a single object
    that the graphql server has access that stays the same object between reload. This container
    object allows the RepositoryInfo to be written in an immutable fashion.
    '''

    def __init__(self, repository_target_info=None, repository=None):
        if repository_target_info != None:
            self.repo_dynamic_obj = check.inst_param(
                load_repository_object_from_target_info(repository_target_info),
                'repo_dynamic_obj',
                DynamicObject,
            )
            self.repo = None
            self.repo_error = None
            self.reload()
        elif repository != None:
            self.repo = repository

    def reload(self):
        if not self.repo_dynamic_obj:
            return
        try:
            self.repo = self.repo_dynamic_obj.load()
            self.repo_error = None
        except:
            self.repo_error = sys.exc_info()

    @property
    def repository(self):
        return self.repo

    @property
    def error(self):
        return self.repo_error

class DagsterGraphQLView(GraphQLView):
    def __init__(self, repository_container, **kwargs):
        super(DagsterGraphQLView, self).__init__(**kwargs)
        self.repository_container = check.inst_param(
            repository_container,
            'repository_container',
            RepositoryContainer,
        )

    def get_context(self):
        return {'repository_container': self.repository_container}


def static_view(path, file):
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), './webapp/build/static/', path), file
    )


def index_view(_path):
    try:
        return send_file(os.path.join(os.path.dirname(__file__), './webapp/build/index.html'))
    except FileNotFoundError:
        text = '''<p>Can't find webapp files. Probably webapp isn't built. If you are using
        dagit, then probably it's a corrupted installation or a bug. However, if you are
        developing dagit locally, you problem can be fixed as follows:</p>

<pre>cd ./python_modules/dagit/dagit/webapp
yarn
yarn build</pre>'''
        return text, 500


def create_app(repository_container):
    app = Flask('dagster-ui')

    schema = create_schema()
    app.add_url_rule(
        '/graphql', 'graphql',
        DagsterGraphQLView.as_view(
            'graphql',
            schema=schema,
            graphiql=True,
            executor=Executor(),
            repository_container=repository_container,
        )
    )
    app.add_url_rule('/static/<path:path>/<string:file>', 'static_view', static_view)
    app.add_url_rule('/<path:_path>', 'index_catchall', index_view)
    app.add_url_rule(
        '/',
        'index',
        index_view,
        defaults={'_path': ''},
    )

    CORS(app)

    return app
