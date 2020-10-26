import os
from abc import ABCMeta
from collections import namedtuple

import six
from dagster import check
from dagster.core.code_pointer import CodePointer
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.serdes import whitelist_for_serdes

# This is a hard-coded name for the special "in-process" location.
# This is typically only used for test, although we may allow
# users to load user code into a host process as well. We want
# to encourage the user code to be in user processes as much
# as possible since that it how this system will be used in prod.
# We used a hard-coded name so that we don't have to create
# made up names for this case.
IN_PROCESS_NAME = "<<in_process>>"


def _assign_grpc_location_name(port, socket, host):
    check.opt_int_param(port, "port")
    check.opt_str_param(socket, "socket")
    check.str_param(host, "host")
    check.invariant(port or socket)
    return "grpc:{host}:{socket_or_port}".format(
        host=host, socket_or_port=(socket if socket else port)
    )


def _assign_loadable_target_origin_name(loadable_target_origin):
    check.inst_param(loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin)

    file_or_module = (
        loadable_target_origin.package_name
        if loadable_target_origin.package_name
        else (
            loadable_target_origin.module_name
            if loadable_target_origin.module_name
            else os.path.basename(loadable_target_origin.python_file)
        )
    )

    return (
        "{file_or_module}:{attribute}".format(
            file_or_module=file_or_module, attribute=loadable_target_origin.attribute
        )
        if loadable_target_origin.attribute
        else file_or_module
    )


class RepositoryLocationOrigin(six.with_metaclass(ABCMeta)):
    """Serializable representation of a RepositoryLocation that can be used to
       uniquely identify the location or reload it in across process boundaries.
    """


@whitelist_for_serdes
class InProcessRepositoryLocationOrigin(
    namedtuple("_InProcessRepositoryLocationOrigin", "code_pointer"), RepositoryLocationOrigin,
):
    """Identifies a repository location constructed in the host process. Should only be
       used in tests.
    """

    def __new__(cls, code_pointer):
        return super(InProcessRepositoryLocationOrigin, cls).__new__(
            cls, check.inst_param(code_pointer, "code_pointer", CodePointer,)
        )

    @property
    def location_name(self):
        return IN_PROCESS_NAME


@whitelist_for_serdes
class PythonEnvRepositoryLocationOrigin(
    namedtuple("_PythonEnvRepositoryLocationOrigin", "loadable_target_origin location_name"),
    RepositoryLocationOrigin,
):
    def __new__(cls, loadable_target_origin, location_name=None):
        return super(PythonEnvRepositoryLocationOrigin, cls).__new__(
            cls,
            check.inst_param(
                loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin
            ),
            check.str_param(location_name, "location_name")
            if location_name
            else _assign_loadable_target_origin_name(loadable_target_origin),
        )


@whitelist_for_serdes
class ManagedGrpcPythonEnvRepositoryLocationOrigin(
    namedtuple(
        "_ManagedGrpcPythonEnvRepositoryLocationOrigin", "loadable_target_origin location_name"
    ),
    RepositoryLocationOrigin,
):
    """Identifies a repository location in a Python environment. Dagster creates a gRPC server
       for these repository locations on startup.
    """

    def __new__(cls, loadable_target_origin, location_name=None):
        return super(ManagedGrpcPythonEnvRepositoryLocationOrigin, cls).__new__(
            cls,
            check.inst_param(
                loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin
            ),
            check.str_param(location_name, "location_name")
            if location_name
            else _assign_loadable_target_origin_name(loadable_target_origin),
        )


@whitelist_for_serdes
class GrpcServerRepositoryLocationOrigin(
    namedtuple("_GrpcServerRepositoryLocationOrigin", "host port socket location_name"),
    RepositoryLocationOrigin,
):
    """Identifies a repository location hosted in a gRPC server managed by the user. Dagster
    is not responsible for managing the lifecycle of the server.
    """

    def __new__(cls, host, port=None, socket=None, location_name=None):
        return super(GrpcServerRepositoryLocationOrigin, cls).__new__(
            cls,
            check.str_param(host, "host"),
            check.opt_int_param(port, "port"),
            check.opt_str_param(socket, "socket"),
            check.str_param(location_name, "location_name")
            if location_name
            else _assign_grpc_location_name(port, socket, host),
        )
