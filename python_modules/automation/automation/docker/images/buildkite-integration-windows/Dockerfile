####################################################################################################
#
# DAGSTER WINDOWS INTEGRATION IMAGE
#
# We use this Dockerfile to build an image for our Buildkite CI/CD pipeline.
#
####################################################################################################

ARG BASE_IMAGE
ARG PYTHON_VERSION
FROM "${BASE_IMAGE}" AS snapshot_builder

# Install git https://stackoverflow.com/a/43681637
# See: https://github.com/git-for-windows/git/releases/tag/v2.30.0.windows.1
RUN Invoke-WebRequest 'https://github.com/git-for-windows/git/releases/download/v2.30.0.windows.1/MinGit-2.30.0-64-bit.zip' -OutFile MinGit.zip
RUN Expand-Archive c:\MinGit.zip -DestinationPath c:\MinGit; \
    $env:PATH = $env:PATH + ';C:\MinGit\cmd\;C:\MinGit\cmd'; \
    Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment\' -Name Path -Value $env:PATH

# Install Chocolatey
ENV chocolateyUseWindowsCompression false
RUN iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1')); \
    choco feature disable --name showDownloadProgress

# # Install gnuwin32-coreutils for make
# RUN choco install -y gnuwin32-coreutils.install
RUN choco install -y make

RUN git clone https://github.com/dagster-io/dagster.git; \
    cd dagster; \
    make install_dev_python_modules

RUN pip freeze --exclude-editable | Out-File -FilePath C:\snapshot-reqs.txt

FROM "${BASE_IMAGE}"

COPY --from=snapshot_builder \snapshot-reqs.txt .

RUN pip install -r C:\snapshot-reqs.txt; \
    Remove-Item C:\snapshot-reqs.txt
