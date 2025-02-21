#
# Copyright (c) 2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import keyring
import yaml

from oslo_log import log as logging

from sysinv.common import exception
from sysinv.db import api as dbapi
from sysinv.helm import base


from k8sapp_distributed_cloud.common import constants as app_constants

LOG = logging.getLogger(__name__)


class DistributedCloudHelm(base.FluxCDBaseHelm):
    """Class to encapsulate helm operations for the Distributed Cloud charts"""

    SUPPORTED_NAMESPACES = base.FluxCDBaseHelm.SUPPORTED_NAMESPACES + \
        [app_constants.HELM_NS_DISTCLOUD]

    SUPPORTED_APP_NAMESPACES = {
        app_constants.HELM_APP_DISTCLOUD: SUPPORTED_NAMESPACES,
    }

    SERVICE_NAME = app_constants.HELM_APP_DISTCLOUD

    SUPPORTED_COMPONENT_OVERRIDES = [
        app_constants.HELM_COMPONENT_LABEL_VALUE_PLATFORM,
        app_constants.HELM_COMPONENT_LABEL_VALUE_APPLICATION
    ]

    DEFAULT_AFFINITY = app_constants.HELM_COMPONENT_LABEL_VALUE_PLATFORM

    KEYRING_SERVICE_ADMIN = 'CGCS'
    KEYRING_SERVICE_AMQP = 'amqp'

    KEYRING_USER_DATABASE = 'database'
    KEYRING_USER_SERVICES = 'services'
    KEYRING_USER_ADMIN = 'admin'
    KEYRING_USER_AMQP = 'rabbit'

    @property
    def CHART(self):
        raise NotImplemented("CHART property not implemented")

    @property
    def HELM_RELEASE(self):
        raise NotImplemented("HELM_RELEASE property not implemented")

    def get_namespaces(self):
        return self.SUPPORTED_NAMESPACES

    def get_overrides(self, namespace=None):
        dbapi_instance = dbapi.get_instance()
        db_app = dbapi_instance.kube_app_get(app_constants.HELM_APP_DISTCLOUD)

        # User chart overrides
        chart_overrides = self._get_helm_overrides(
            dbapi_instance,
            db_app,
            self.CHART,
            app_constants.HELM_NS_DISTCLOUD,
            'user_overrides')

        user_affinity = chart_overrides.get(app_constants.HELM_COMPONENT_LABEL,
                                            self.DEFAULT_AFFINITY)

        if user_affinity in self.SUPPORTED_COMPONENT_OVERRIDES:
            affinity = user_affinity
        else:
            LOG.warn(f"User override value {user_affinity} "
                     f"for {app_constants.HELM_COMPONENT_LABEL} is invalid, "
                     f"using default value {self.DEFAULT_AFFINITY}")
            affinity = self.DEFAULT_AFFINITY

        overrides = {
            app_constants.HELM_NS_DISTCLOUD: {
                app_constants.HELM_LABEL_PARAMETER: {
                    app_constants.HELM_COMPONENT_LABEL: affinity
                },
                "endpoints": self._get_endpoint_overrides()
            }
        }

        if namespace in self.SUPPORTED_NAMESPACES:
            return overrides[namespace]

        if namespace:
            raise exception.InvalidHelmNamespace(chart=self.CHART,
                                                 namespace=namespace)
        return overrides

    @staticmethod
    def _get_helm_overrides(dbapi_instance, app, chart, namespace,
                            type_of_overrides):
        """Helper function for querying helm overrides from db."""
        helm_overrides = {}
        try:
            overrides = dbapi_instance.helm_override_get(
                app_id=app.id,
                name=chart,
                namespace=namespace,
            )[type_of_overrides]

            if isinstance(overrides, str):
                helm_overrides = yaml.safe_load(overrides)
        except exception.HelmOverrideNotFound:
            LOG.debug("Overrides for this chart not found, nothing to be done.")
        return helm_overrides

    def _get_endpoint_overrides(self):
        """Get common endpoint helm overrides"""

        admin_ks_password=keyring.get_password(self.KEYRING_SERVICE_ADMIN,
                                               self.KEYRING_USER_ADMIN)
        rabbitmq_password=keyring.get_password(self.KEYRING_SERVICE_AMQP,
                                               self.KEYRING_USER_AMQP)
        service_db_password=keyring.get_password(self.CHART,
                                                 self.KEYRING_USER_DATABASE)
        service_ks_password=keyring.get_password(self.CHART,
                                                 self.KEYRING_USER_SERVICES)

        endpoints = {
            "oslo_db": {
                "auth": {
                    "admin": {
                        "password": service_db_password,
                    },
                    self.CHART: {
                        "password": service_db_password,
                    }
                }
            },
            "oslo_messaging": {
                "auth": {
                    "admin": {
                        "password": rabbitmq_password,
                    },
                    self.CHART: {
                        "password": rabbitmq_password,
                    }
                }
            },
            "identity": {
                "auth": {
                    "admin": {
                        "password": admin_ks_password,
                    },
                    self.CHART: {
                        "password": service_ks_password,
                    }
                }
            }
        }

        return endpoints