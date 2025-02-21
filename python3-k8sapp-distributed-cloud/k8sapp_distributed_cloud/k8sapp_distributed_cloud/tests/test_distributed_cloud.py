#
# Copyright (c) 2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from sysinv.db import api as dbapi
from sysinv.tests.db import base as dbbase
from sysinv.tests.db import utils as dbutils
from sysinv.tests.helm import base

from k8sapp_distributed_cloud.tests import test_plugins


class DistributedCloudTestCase(test_plugins.K8SAppDistributedCloudAppMixin,
                               base.HelmTestCaseMixin):

    def setUp(self):
        super().setUp()
        self.app = dbutils.create_test_app(name='distributed-cloud')
        self.dbapi = dbapi.get_instance()


class DistributedCloudTestCaseDummy(DistributedCloudTestCase,
                                    dbbase.ProvisionedControllerHostTestCase):
    # without a test zuul will fail
    def test_dummy(self):
        pass
