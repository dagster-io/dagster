# Local development setup

<ol>
<li>Create and activate virtualenv

```
python3 -m venv dagsterenv
source dagsterenv/bin/activate
```

</li>

<li>Install dagster locally and install dev tools

```
pip install -e ./dagster
pip install -r ./dagster/dev-requirements.txt
```
</li>


<li>Install pre-commit hooks

```
pre-commit install
```
</li>


<li>Run tests

```
tox
```
</li>


</ol>


## Developing docs

```
cd docs
make livehtml
```
