# /bin/bash
pushd ..
rm -r -f grpc
git clone https://github.com/grpc/grpc.git --depth 1
pushd grpc
git submodule update --init
pip install -rrequirements.txt
GRPC_PYTHON_BUILD_WITH_CYTHON=1 GRPC_PYTHON_CFLAGS="-g" pip install .
popd
popd
pip install protobuf\<4