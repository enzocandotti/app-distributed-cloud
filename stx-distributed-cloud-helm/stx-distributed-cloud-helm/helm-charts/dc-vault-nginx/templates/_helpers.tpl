{{- define "dc-vault-nginx.fullname" -}}
{{- if .Release.Name -}}
{{ .Release.Name }}
{{- else -}}
dc-vault-nginx
{{- end -}}
{{- end }}

{{- define "dc-vault-nginx.labels" -}}
app.kubernetes.io/name: {{ default "dc-vault-nginx" .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name | default "dc-vault-nginx" }}
app.kubernetes.io/version: {{ .Chart.AppVersion | default "1.0.0" }}
app.kubernetes.io/managed-by: {{ .Release.Service | default "Helm" }}
{{- end }}

{{- define "dc-vault-nginx.serverNames" -}}
{{- range $index, $host := .Values.ingress.hosts -}}
{{- if $index -}} {{ " " }}{{- end -}}{{ $host.host }}
{{- end -}}
{{- end }}