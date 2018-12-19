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

import pickle

from cloudpickle import CloudPickler

from .module_dependency import ModuleDependencyAnalyzer
from .utils import create_mod_data


def serialize(obj):
    """Serializes an object and all of its dependencies.

    Args:
        obj (object): The object to serialize

    Returns:
        (bytes): The serialized representation of the object and its dependencies.
    """
    module_manager = ModuleDependencyAnalyzer()

    pickled_obj = CloudPickler.dump(obj)

    for module in pickled_obj.modules:
        module_manager.add(module.__name__)

    module_paths = module_manager.get_and_clear_paths()

    module_data = create_mod_data(module_paths)

    return pickle.dumps({'obj': pickled_obj, 'module_data': module_data}, -1)


def deserialize(pickled_obj):
    #   https://github.com/pywren/pywren/blob/master/pywren/jobrunner/jobrunner.py#L89
    pass
