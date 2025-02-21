# DC Services Containerization

This tutorial provides a step-by-step guide on containerizing DC Services using the
app-distributed-cloud prototype. The objective is to ensure the interaction between
the dcmanager-api pod and the dcmanager-manager pod while integrating essential
platform components such as dcmanager-client, keystone, rabbitmq, and certificates.

This use the minikube build environment for WRCP: <https://confluence.wrs.com/pages/viewpage.action?pageId=165764450>

Recommended: have all packages built before setting up the new app-distributed-cloud

## Configure prototype in the WRCP build environment

- Prototype: `/folk/cgts/users/mpeters/design/platform/distcloud/app-distributed-cloud/`
- Copy app-distributed-cloud directory to `$MY_REPO/stx`
- Add app-distributed-cloud to manifest `$MY_REPO/../.repo/manifests/default.xml`

  ```xml
  <project remote="starlingx"  name="app-distributed-cloud.git"               path="cgcs-root/stx/app-distributed-cloud"/>
  ```

- Add app-distributed-cloud to project.list: $MY_REPO/../.repo/project.list

cgcs-root/stx/app-distributed-cloud

## Build Required Packages

Note.: If package builds fail, you can retrieve the *.deb file and rebuild it:

`localdisk/loadbuild/jenkins/wrcp-master-debian/latest_build/export/outputs/aptly/deb-local-build/pool/main/<initial_letter>/<package>/<package.deb>`

Copy to `aptly/public/deb-local-build-{}/pool/main/` and `localdisk/loadbuild/<user>/wrcp-env/std` in your env

- Required packages:

```bash
build-pkgs -p cgcs-patch,cgts-client,distributedcloud-client,distributedcloud,fm-api,fm-common,fm-rest-api,nfv,nova-api-proxy,pci-irq-affinity-agent,python-fmclient,python3-networking-avs,python3-oidcauthtools,python3-vswitchclient,software-client,software,sysinv,tsconfig
```

- Build Distributed Cloud application bundle

```bash
build-pkgs -c -p python3-k8sapp-distributed-cloud,stx-distributed-cloud-helm
```

## Build wheels

```bash
$MY_REPO/build-tools/build-wheels/build-wheel-tarball.sh --keep-image --cache --os debian
```

Note.: You can create the helm charts using: `build-helm-charts.sh`

## Container image build: <https://confluence.wrs.com/display/CE/How+to+build+docker+images>

```bash
BUILD_OS=debian
BUILD_STREAM=stable
BRANCH=master
BASE_IMAGE=starlingx/stx-${BUILD_OS}:${BRANCH}-${BUILD_STREAM}-latest
WHEELS=$MY_WORKSPACE/std/build-wheels-debian-stable/stx-debian-stable-wheels.tar
DOCKER_USER=${USER}
DOCKER_REGISTRY=admin-2.cumulus.wrs.com:30093

# Pull base image
docker pull $BASE_IMAGE

# Login to the registry for pushing the container image
docker login -u ${DOCKER_USER} ${DOCKER_REGISTRY}

$MY_REPO/build-tools/build-docker-images/build-stx-images.sh \
    --os ${BUILD_OS} \
    --stream ${BUILD_STREAM} \
    --base ${BASE_IMAGE} \
    --wheels ${WHEELS} \
    --user ${DOCKER_USER} \
    --registry ${DOCKER_REGISTRY} \
    --no-pull-base --cache \
    --push --latest \
    --only "stx-distributed-cloud"
```

## Build WRCP iso

```bash
build-image
```

## Disable Service Management

With the new WRCP ISO installed, you need to disable the DCManager services that are being containerized.

```bash
source /etc/platform/openrc

sudo sm-unmanage service dcmanager-manager
sudo sm-unmanage service dcmanager-api
sudo sm-unmanage service dcmanager-audit
sudo sm-unmanage service dcmanager-audit-worker
sudo sm-unmanage service dcmanager-orchestrator
sudo sm-unmanage service dcmanager-state

sudo sm-unmanage service dcorch-engine
sudo sm-unmanage service dcorch-engine-worker
sudo sm-unmanage service dcorch-sysinv-api-proxy
sudo sm-unmanage service dcorch-patch-api-proxy
sudo sm-unmanage service dcorch-identity-api-proxy

sudo sm-unmanage service dcdbsync-api


sudo pkill -f ^".*/bin/dcmanager.*"
sudo pkill -f ^".*/bin/dcorch.*"
sudo pkill -f ^".*/bin/dcdbsync.*"
```

## Platform Setup

```bash
system host-label-assign controller-0 starlingx.io/distributed-cloud=enabled
system host-label-assign controller-1 starlingx.io/distributed-cloud=enabled
```

## Create the namespace and default registry (avoid issues)

```bash
# Create distributed-cloud namespace

kubectl create namespace distributed-cloud

# Create default-registry-key secret | if using registry.local:9001

kubectl create secret docker-registry default-registry-key \
  --docker-server=registry.local:9001 \
  --docker-username=admin \
  --docker-password=${OS_PASSWORD} \
  --namespace=distributed-cloud
```

## Distributed Cloud Application Deployment (development)

```bash
# Configure Docker Image (using Matt's image)

DOCKER_REGISTRY=admin-2.cumulus.wrs.com:30093
DOCKER_USER=mpeters
DOCKER_ADMIN_IMAGE=${DOCKER_REGISTRY}/${DOCKER_USER}/stx-distributed-cloud:dev-debian-stable-latest
DOCKER_IMAGE=registry.local:9001/docker.io/starlingx/stx-distributed-cloud:master-debian-stable-latest

sudo docker login registry.local:9001

sudo docker image pull ${DOCKER_ADMIN_IMAGE}
sudo docker image tag ${DOCKER_ADMIN_IMAGE} ${DOCKER_IMAGE}
sudo docker image push ${DOCKER_IMAGE}
```

```bash
system application-upload /usr/local/share/applications/helm/distributed-cloud-24.09-0.tgz

# Set Password Variables

ADMIN_KS_PASSWORD=$(keyring get CGCS admin)
RABBITMQ_PASSWORD=$(keyring get amqp rabbit)
DCMANAGER_DB_PASSWORD=$(keyring get dcmanager database)
DCMANAGER_KS_PASSWORD=$(keyring get dcmanager services)
DCORCH_DB_PASSWORD=$(keyring get dcorch database)
DCORCH_KS_PASSWORD=$(keyring get dcorch services)

DOCKER_IMAGE=registry.local:9001/docker.io/starlingx/stx-distributed-cloud:master-debian-stable-latest3

ADMIN_KS_PASSWORD=$(keyring get CGCS admin)
RABBITMQ_PASSWORD=$(keyring get amqp rabbit)
DCMANAGER_DB_PASSWORD=$(keyring get dcmanager database)
DCMANAGER_KS_PASSWORD=$(keyring get dcmanager services)
DCORCH_DB_PASSWORD=$(keyring get dcorch database)
DCORCH_KS_PASSWORD=$(keyring get dcorch services)

cat<<EOF>dcmanager.yaml
images:
  tags:
    dcmanager: ${DOCKER_IMAGE}
    ks_user: ${DOCKER_IMAGE}
    ks_service: ${DOCKER_IMAGE}
    ks_endpoints: ${DOCKER_IMAGE}
    dcmanager_db_sync: ${DOCKER_IMAGE}
    db_init: ${DOCKER_IMAGE}
    db_drop: ${DOCKER_IMAGE}
  pullPolicy: Always
pod:
  image_pull_secrets:
    default:
      - name: default-registry-key
  tolerations:
    dcmanager:
      enabled: true
conf:
  dcmanager:
    DEFAULT:
      log_config_append: /etc/dcmanager/logging.conf
      transport_url: rabbit://guest:${RABBITMQ_PASSWORD}@controller.internal:5672
      auth_strategy: keystone
      playbook_timeout: 3600
      use_usm: False
      workers: 1
      orch_workers: 1
      state_workers: 1
      audit_workers: 1
      audit_worker_workers: 1
    endpoint_cache:
      password: ${DCMANAGER_KS_PASSWORD}
    database:
      connection_recycle_time: 3600
      max_pool_size: 105
      max_overflow: 100
    keystone_authtoken:
      auth_version: v3
      auth_type: password
dependencies:
  static:
    api:
      jobs:
        - dcmanager-ks-user
        - dcmanager-ks-service
        - dcmanager-ks-endpoints
    ks_endpoints:
      jobs:
        - dcmanager-ks-user
        - dcmanager-ks-service
endpoints:
  cluster_domain_suffix: cluster.local
  oslo_db:
    auth:
      admin:
        username: admin-dcmanager
        password: ${DCMANAGER_DB_PASSWORD}
      dcmanager:
        username: admin-dcmanager
        password: ${DCMANAGER_DB_PASSWORD}
    hosts:
      default: postgresql
    host_fqdn_override:
      default: controller.internal
    port:
      postgresql:
        default: 5432
    path: /dcmanager
    scheme: postgresql+psycopg2
  oslo_messaging:
    auth:
      admin:
        username: guest
        password: ${RABBITMQ_PASSWORD}
      dcmanager:
        username: guest
        password: ${RABBITMQ_PASSWORD}
    hosts:
      default: rabbitmq
    host_fqdn_override:
      default: controller.internal
    path: /
    scheme: rabbit
    port:
      amqp:
        default: 5672
      http:
        default: 15672
  identity:
    name: keystone
    auth:
      admin:
        username: admin
        password: ${ADMIN_KS_PASSWORD}
        region_name: RegionOne
        project_name: admin
        user_domain_name: Default
        project_domain_name: Default
      dcmanager:
        role: admin
        username: dcmanager
        password: ${DCMANAGER_KS_PASSWORD}
        region_name: RegionOne
        project_name: services
        user_domain_name: Default
        project_domain_name: Default
    hosts:
      default: keystone-api
      public: keystone
    host_fqdn_override:
      default: controller.internal
    path:
      default: /v3
    scheme:
      default: http
    port:
      api:
        default: 80
        internal: 5000
  dcmanager:
    name: dcmanager
    hosts:
      default: dcmanager-api
      public: dcmanager
    host_fqdn_override:
      default: null
    path:
      default: /v1.0
    scheme:
      default: 'http'
    port:
      api:
        default: 8119
        public: 80
EOF



cat<<EOF>dcorch.yaml
images:
  tags:
    dcorch: ${DOCKER_IMAGE}
    ks_user: ${DOCKER_IMAGE}
    ks_service: ${DOCKER_IMAGE}
    ks_endpoints: ${DOCKER_IMAGE}
    dcorch_db_sync: ${DOCKER_IMAGE}
    db_init: ${DOCKER_IMAGE}
    db_drop: ${DOCKER_IMAGE}
  pullPolicy: Always
pod:
  image_pull_secrets:
    default:
      - name: default-registry-key
  tolerations:
    dcorch:
      enabled: true
  replicas:
    dcorch_engine_worker: 1
    dcorch_sysinv_api_proxy: 1
    dcorch_identity_api_proxy: 1
    dcorch_patch_api_proxy: 1
    dcorch_usm_api_proxy: 1
conf:
  dcorch:
    DEFAULT:
      log_config_append: /etc/dcorch/logging.conf
      transport_url: rabbit://guest:${RABBITMQ_PASSWORD}@controller.internal:5672
      auth_strategy: keystone
      playbook_timeout: 3600
      use_usm: False
    endpoint_cache:
      password: ${DCMANAGER_KS_PASSWORD}
    database:
      connection_recycle_time: 3600
      max_pool_size: 105
      max_overflow: 100
    keystone_authtoken:
      auth_version: v3
      auth_type: password
dependencies:
  static:
    api:
      jobs:
        - dcorch-ks-user
        - dcorch-ks-service
        - dcorch-ks-endpoints
    ks_endpoints:
      jobs:
        - dcorch-ks-user
        - dcorch-ks-service

endpoints:
  cluster_domain_suffix: cluster.local
  oslo_db:
    auth:
      admin:
        username: admin-dcorch
        password: ${DCORCH_DB_PASSWORD}
      dcorch:
        username: admin-dcorch
        password: ${DCORCH_DB_PASSWORD}
      dcmanager:
        username: admin-dcmanager
        password: ${DCMANAGER_DB_PASSWORD}
    hosts:
      default: postgresql
    host_fqdn_override:
      default: controller.internal
    port:
      postgresql:
        default: 5432
    path: /dcorch
    scheme: postgresql+psycopg2
  oslo_messaging:
    auth:
      admin:
        username: guest
        password: ${RABBITMQ_PASSWORD}
      dcmanager:
        username: guest
        password: ${RABBITMQ_PASSWORD}
    hosts:
      default: rabbitmq
    host_fqdn_override:
      default: controller.internal
    path: /
    scheme: rabbit
    port:
      amqp:
        default: 5672
      http:
        default: 15672
  identity:
    name: keystone
    auth:
      admin:
        username: admin
        password: ${ADMIN_KS_PASSWORD}
        region_name: RegionOne
        project_name: admin
        user_domain_name: Default
        project_domain_name: Default
      dcorch:
        role: admin
        username: dcorch
        password: ${DCORCH_KS_PASSWORD}
        region_name: RegionOne
        project_name: services
        user_domain_name: Default
        project_domain_name: Default
    hosts:
      default: keystone-api
      public: keystone
    host_fqdn_override:
      default: controller.internal
    path:
      default: /v3
    scheme:
      default: http
    port:
      api:
        default: 80
        internal: 5000
  dcorch:
    name: dcorch
    hosts:
      default: dcorch-api
      public: dcorch
    host_fqdn_override:
      default: null
    path:
      default: /v1.0
    scheme:
      default: 'http'
    port:
      dcorch_api:
        default: 8118
        public: 80
EOF
```

```bash
system helm-override-update distributed-cloud dcmanager distributed-cloud --values dcmanager.yaml
system helm-override-update distributed-cloud dcorch distributed-cloud --values dcorch.yaml

system helm-override-show distributed-cloud dcmanager distributed-cloud
system helm-override-show distributed-cloud dcorch distributed-cloud
```
# Possible issue with ceph-pool-kube-rbd secret
```bash
kubectl create secret generic ceph-pool-kube-rbd --namespace=kube-system
```
# Create system-local-ca secret
```bash

cp /etc/ssl/certs/dc-adminep-root-ca.pem /home/sysadmin

kubectl -n distributed-cloud create secret generic system-local-ca --from-file=ca.crt=/home/sysadmin/dc-adminep-root-ca.pem
```

# Apply app-distributed-cloud
```bash
system application-apply distributed-cloud
system application-show distributed-cloud
```

# To remove
```bash
system application-remove distributed-cloud
system application-delete distributed-cloud
```

## Check dcmanager endpoints

```bash
openstack endpoint list | grep dcmanager
```

## Check if dcmanager-api endpoint works

```bash
kubectl get svc dcmanager-api -n distributed-cloud
kubectl get endpoints dcmanager-api -n distributed-cloud

# Get Token
openstack token issue

curl -i http://<endpoint>/v1.0/subclouds -X GET -H "Content-Type: application/json" -H "Accept: application/json" -H "X-Auth-Token:${TOKEN}"
```

## Configure dcmanager-client

File: /usr/lib/python3/dist-packages/dcmanagerclient/api/v1/client.py

```python
_DEFAULT_DCMANAGER_URL = (
    "http://dcmanager-api.distributed-cloud.svc.cluster.local:8119/v1.0"
)

# delete if not dcmanager_url: to always set default
dcmanager_url = _DEFAULT_DCMANAGER_URL
```

## Check dcmanager-manager is working

```bash
dcmanager subcloud-group add --name test
dcmanager subcloud update --group 2 subcloud2-stx-latest
```

## Distributed Cloud Helm Deployment (manual)

- Create the helm chart

```bash
# inside app-distributed-cloud/stx-distributed-cloud-helm/stx-distributed-cloud-helm/helm-charts/dcmanager
helm package .
helm install dcmanager dcmanager-0.1.0.tgz --namespace distributed-cloud --values dcmanager.yaml
```

## Check secrets
```bash
kubectl -n distributed-cloud get secret dcmanager-etc --output="jsonpath={.data.dcmanager\.conf}" | base64 --decode
kubectl -n distributed-cloud get secret dcmanager-rabbitmq-admin --output="jsonpath={.data.RABBITMQ_CONNECTION}" | base64 --decode
kubectl -n distributed-cloud get secret dcmanager-db-admin --output="jsonpath={.data.DB_CONNECTION}" | base64 --decode
kubectl -n distributed-cloud get secret dcmanager-keystone-admin --output="jsonpath={.data.OS_PASSWORD}" | base64 --decode
```
## Check Logs
```bash
kubectl -n distributed-cloud logs -l application=dcmanager,component=api
kubectl -n distributed-cloud logs -l application=dcmanager,component=manager
kubectl -n distributed-cloud logs -l application=dcmanager,component=audit
kubectl -n distributed-cloud logs -l application=dcmanager,component=state
kubectl -n distributed-cloud logs -l application=dcmanager,component=orchestrator

helm status --show-resources dcmanager --namespace distributed-cloud
```
