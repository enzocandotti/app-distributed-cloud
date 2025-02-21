#
# Copyright (c) 2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from . import base

from k8sapp_distributed_cloud.common import constants as app_constants


class DCManagerHelm(base.DistributedCloudHelm):

    @property
    def CHART(self):
        return app_constants.HELM_CHART_DCMANAGER

    @property
    def HELM_RELEASE(self):
        return app_constants.FLUXCD_HELM_RELEASE_DCMANAGER
