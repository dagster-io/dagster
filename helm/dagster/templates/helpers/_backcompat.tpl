{{/*
Create a layer to resolve deprecated names. With release 1.4, the following `values.yaml` paths were
changed:

- .dagit -> .dagsterWebserver
- .ingress.dagit -> .ingress.dagsterWebserver
- .ingress.readOnlyDagit -> .ingress.readOnlyDagsterWebserver

This template defines a dictionary containing all the renamed paths. Each
renamed path contains the merge of the old path and the new path.

Because this dictionary is a complex data structure rather than a string, it
needs to be packaged using JSON in order to properly "import" it in another
template. Recommended usage is to deserialize using `mustFromJson` and assign
to the variable `$_` for unobtrusiveness. For example, the following will
render correctly if the user passed in "dagit" values:

    {{ $_ := include "dagster.backcompat" . | mustFromJson }}
    dagster-webserver -h 0.0.0.0 -p {{ $_.Values.dagsterWebserver.service.port }}

*/}}
{{- define "dagster.backcompat" -}}
{{ $dagsterWebserver := merge (coalesce .Values.dagit dict) .Values.dagsterWebserver }}
{{ $ingressDagsterWebserver := merge (coalesce .Values.ingress.dagit dict) .Values.ingress.dagsterWebserver }}
{{ $ingressReadOnlyDagsterWebserver := merge .Values.ingress.readOnlyDagsterWebserver (coalesce .Values.ingress.readOnlyDagit dict) }}
{{ mustToJson (dict "Values" (dict "dagsterWebserver" $dagsterWebserver "ingress" (dict "dagsterWebserver" $ingressDagsterWebserver "readOnlyDagsterWebserver" $ingressReadOnlyDagsterWebserver))) }}
{{- end -}}
