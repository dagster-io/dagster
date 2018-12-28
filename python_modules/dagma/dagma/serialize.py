"""Custom serializer for dagma.

Uses the cloudpickle module and the multyvac ModuleDependencyAnalyzer, included here to avoid
taking a dubious dependency, following the pattern used by the PyWren team. For the avoidance of
any doubt, the PyWren license is included below:

Copyright 2018 PyWren Team

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in
   the documentation and/or other materials provided with the
   distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived
   from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

"""

import os
import pickle
import shutil
import sys

from io import BytesIO as StringIO

from cloudpickle import CloudPickler

from .module_dependency import ModuleDependencyAnalyzer
from .utils import (
    b64str_to_bytes,
    create_mod_data,
)


def serialize(obj):
    """Serializes an object and all of its dependencies.

    Args:
        obj (object): The object to serialize

    Returns:
        (bytes): The serialized representation of the object and its dependencies.
    """
    module_manager = ModuleDependencyAnalyzer()

    stringio = StringIO()
    pickler = CloudPickler(stringio, -1)

    pickler.dump(obj)

    for module in pickler.modules:
        module_manager.add(module.__name__)

    module_paths = module_manager.get_and_clear_paths()

    module_data = create_mod_data(module_paths)

    return pickle.dumps({'obj': stringio, 'module_data': module_data}, -1)


def deserialize(pickled_obj, ):
    all_loaded = pickle.loads(pickled_obj)

    PYTHON_MODULE_PATH = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '..', '..', 'pymodules'
    )
    shutil.rmtree(PYTHON_MODULE_PATH, True)  # delete old modules
    os.mkdir(PYTHON_MODULE_PATH)
    sys.path.append(PYTHON_MODULE_PATH)

    for m_filename, m_data in all_loaded['module_data'].items():
        m_path = os.path.dirname(m_filename)
        if len(m_path) > 0 and m_path[0] == "/":
            m_path = m_path[1:]
        to_make = os.path.join(PYTHON_MODULE_PATH, m_path)

        try:
            os.makedirs(to_make)
        except OSError as e:
            if e.errno == 17:
                pass
            else:
                raise e
        full_filename = os.path.join(to_make, os.path.basename(m_filename))
        with open(full_filename, 'wb') as fid:
            fid.write(b64str_to_bytes(m_data))

    #   https://github.com/pywren/pywren/blob/master/pywren/jobrunner/jobrunner.py#L89
    pass


#     # logger.info("Finished wrting {} module files".format(len(d['module_data'])))
#     # logger.debug(subprocess.check_output("find {}".format(PYTHON_MODULE_PATH), shell=True))
#     # logger.debug(subprocess.check_output("find {}".format(os.getcwd()), shell=True))

#     # now unpickle function; it will expect modules to be there
#     loaded_func = pickle.loads(loaded_func_all['func'])

#     extra_get_args = {}
#     if data_byte_range is not None:
#         range_str = 'bytes={}-{}'.format(*data_byte_range)
#         extra_get_args['Range'] = range_str

#     data_download_time_t1 = time.time()
#     data_obj_stream = get_object_with_backoff(s3_client, bucket=data_bucket,
#                                               key=data_key,
#                                               **extra_get_args)
#     # FIXME make this streaming
#     loaded_data = pickle.loads(data_obj_stream['Body'].read())
#     data_download_time_t2 = time.time()
#     write_stat('data_download_time',
#                data_download_time_t2-data_download_time_t1)

#     #print("loaded")
#     y = loaded_func(loaded_data)
#     #print("success")
#     output_dict = {'result' : y,
#                    'success' : True,
#                    'sys.path' : sys.path}
#     pickled_output = pickle.dumps(output_dict)
