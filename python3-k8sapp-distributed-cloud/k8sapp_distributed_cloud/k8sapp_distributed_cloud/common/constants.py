#
# Copyright (c) 2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# Helm: Supported charts:
# These values match the names in the chart package's Chart.yaml
HELM_CHART_DCMANAGER = 'dcmanager'
HELM_CHART_DCORCH = 'dcorch'

# FluxCD
FLUXCD_HELM_RELEASE_DCMANAGER = 'dcmanager'
FLUXCD_HELM_RELEASE_DCORCH = 'dcorch'

# Namespace to deploy the application
HELM_NS_DISTCLOUD = 'distributed-cloud'

# Application Name
HELM_APP_DISTCLOUD = 'distributed-cloud'

# Application Services
HELM_SERVICE_DCMANAGER_API = "dcmanager-api"

# Application component label
HELM_LABEL_PARAMETER = 'labels'
HELM_COMPONENT_LABEL = 'app.starlingx.io/component'
HELM_COMPONENT_LABEL_VALUE_PLATFORM = 'platform'
HELM_COMPONENT_LABEL_VALUE_APPLICATION = 'application'
