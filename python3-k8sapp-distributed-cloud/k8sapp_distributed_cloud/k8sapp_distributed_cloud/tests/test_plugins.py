#
# Copyright (c) 2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from sysinv.tests.db import base as dbbase

from k8sapp_distributed_cloud.common import constants as app_constants


class K8SAppDistributedCloudAppMixin(object):
    app_name = app_constants.HELM_APP_DISTCLOUD
    path_name = app_name + '.tgz'

    # pylint: disable=invalid-name,useless-parent-delegation
    def setUp(self):
        super().setUp()

    def test_stub(self):
        # Replace this with a real unit test.
        pass


# Test Configuration:
# - Controller
# - IPv6
# - Ceph Storage
# - distributed-cloud app
class K8sAppDistributedCloudControllerTestCase(K8SAppDistributedCloudAppMixin,
                                               dbbase.BaseIPv6Mixin,
                                               dbbase.BaseCephStorageBackendMixin,
                                               dbbase.ControllerHostTestCase):
    pass


# Test Configuration:
# - AIO
# - IPv4
# - Ceph Storage
# - distributed-cloud app
class K8SAppDistributedCloudAIOTestCase(K8SAppDistributedCloudAppMixin,
                                        dbbase.BaseCephStorageBackendMixin,
                                        dbbase.AIOSimplexHostTestCase):
    pass
