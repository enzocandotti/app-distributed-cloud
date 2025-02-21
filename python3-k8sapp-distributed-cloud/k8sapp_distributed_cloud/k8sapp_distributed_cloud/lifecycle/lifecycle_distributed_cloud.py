#
# Copyright (c) 2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
# All Rights Reserved.
#

""" System Inventory App lifecycle operator."""

from oslo_log import log as logging

from sysinv.common import constants as c
from sysinv.helm import lifecycle_base as base
from sysinv.helm import lifecycle_utils

from k8sapp_distributed_cloud.common import constants as app_constants

LOG = logging.getLogger(__name__)


class DistributedCloudAppLifecycleOperator(base.AppLifecycleOperator):

    def app_lifecycle_actions(self, context, conductor_obj,
                              app_op, app, hook_info):
        """Perform lifecycle actions for an operation

        :param context: request context, can be None
        :param conductor_obj: conductor object, can be None
        :param app_op: AppOperator object
        :param app: AppOperator.Application object
        :param hook_info: LifecycleHookInfo object

        """

        if hook_info.lifecycle_type == c.APP_LIFECYCLE_TYPE_OPERATION:
            if hook_info.operation == c.APP_REMOVE_OP:
                if hook_info.relative_timing == c.APP_LIFECYCLE_TIMING_POST:
                    self._post_remove(app_op)

        super().app_lifecycle_actions(context, conductor_obj,
                                      app_op, app, hook_info)

    @staticmethod
    def _post_remove(app_op):
        # Helm doesn't delete the namespace. To clean up after
        # application-remove, we need to explicitly delete it.

        LOG.debug(f"Executing post_remove for {app_constants.HELM_APP_DISTCLOUD} app")
        lifecycle_utils.delete_namespace(app_op, app_constants.HELM_NS_DISTCLOUD)
