# Developer Guide

These instructions are for contributing to this repository. See main README.md for usage.

## Manual

```bash
cd src/docker
docker-compose build
docker-compose up
```

## Test

### CI

CI will trigger on pushes to PRs

### Local

To test locally:

```bash
cd src/python
./bin/lint.sh
python3 -m pytest test
```

This is expected to change as full docker-based testing lands

### AWS

* Modify `src/bootstraps/core/graphistry.yml` on the checkout step do use the branch:  `git clone -b mybranch`
* Push your branch
* In CloudFormation, upload your modified `graphistry.yml``

## Aligned base versions

For faster AWS launches and Graphistry Enterprise, we:

- Keep the docker base in sync w/ AWS version & enterprise version:
  * docker-compose.yml: `GRAPHISTRY_FORGE_BASE_VERSION`
  * Dockerfile: `GRAPHISTRY_FORGE_BASE_VERSION`
  * Set both to the appropriate Graphistry (or sufficient Python) base, e.g., `v2.39.12-11.4`

- Update aws version (bootstraps/*/graphistry.yml) by pointing to that version's region AMIs via bootstraps/scripts/graphistry-ami-list.sh
  * Setup: `apt-get install awscli jq` and `aws configure`
  * Run `src/bootstraps/scripts $ VERSION=2.36.6-11.0 ./graphistry-ami-list.sh`
  * Paste into `src/bootstraps/core,neptune/graphistry.yml`
  * Update `src/docker/docker-compose.yml::GRAPHISTRY_FORGE_BASE_VERSION`

## DockerHub publish action

`.github/workflows/dockerhubpublish.yml` builds and pushes `graphistry/graph-app-kit-st` as `v<tag>-<cuda>` and `latest-<cuda>`, where `<cuda>` is a `graphistry-forge-base` tag suffix (currently `13` and `12`).

**Normal path: driven by graphistry CI.** graphistry/graphistry's `base.yml` (`push_gak_tag` + `trigger-gak-build` jobs, on a `ci`-labeled PR, dispatch, or `workflow_call`) tags this repo with the graphistry `VERSION`, then dispatches this workflow on `master` with `cuda_versions '["13", "12"]'` using the PAT in graphistry's `GRAPHISTRY_GHA_CI_GAK` secret, and polls the run for up to 30 minutes. graphistry's release then builds its `graph-app-kit-*` app images on top of the published `v<VERSION>-<cuda>` image. Keep the workflow name `build&publishtoDockerHub`, the `workflow_dispatch` trigger, and master as the dispatch ref, or that chain breaks; anything that holds a dispatched run (for example a required reviewer) must clear within that 30-minute budget.

**Manual path** (rebuild or fallback). Ahead of time:

* Merged into master
* The workflow builds on `graphistry/graphistry-forge-base:v<tag>-<cuda>` (it overrides the `GRAPHISTRY_FORGE_BASE_VERSION` default from the `Dockerfile`/`docker-compose.yml`), so the release tag must match a forge-base tag that exists for every CUDA version you publish. Suffixed tags such as `2.39.12.1` only work if a matching base tag exists.

Publish:

1. `git tag 2.39.12 && git push origin 2.39.12` from master
  * Use the tag of the Graphistry version you are building on
  * Note lack of `v`: the image is published as `v2.39.12-<cuda>`
2. In GitHub Actions, run `build&publishtoDockerHub` from **master** (optionally pass `cuda_versions`, e.g. `["13"]`; each value must be `N` or `N.N`). The version comes from the latest tag.
3. If the `dockerhub-publish` environment has required reviewers, one approves the run

Dispatches from any other branch or tag are skipped. Pushing a tag no longer publishes on its own.

See [current tags](https://hub.docker.com/r/graphistry/graph-app-kit-st/tags) and available [base tags](https://hub.docker.com/r/graphistry/graphistry-forge-base/tags)

## AWS Publish action

`.github/workflows/publish.yml` uploads the CloudFormation templates (`src/bootstraps/{core,neptune}/{graphistry,minimal}.yml`) to `s3://graph-app-kit-repo-public/templates/latest/`. The README "Launch Stack" buttons point at that path, so it is what customers deploy.

* Runs on merge to `master` when a template (or the workflow) changes, or by manual dispatch **from master**. Other refs are skipped, and PR labels no longer publish.
* Every run waits in the `publish-templates` environment for a required reviewer to approve.
* AWS access uses GitHub OIDC. No AWS keys are stored in GitHub.

To test template changes before merge, upload your branch's template by hand to CloudFormation (see "Test / AWS" above). Don't publish it to `templates/latest/`.

### One-time setup (repo admin + AWS admin)

**Order matters.** GitHub auto-creates a missing environment with *no* protection the first time any workflow, on any branch, references it. So lock both environments down before the IAM role exists and before merging the workflow change. Merging also triggers a publish run immediately, because the change touches `publish.yml`.

1. **Create and lock the GitHub environments** (Settings → Environments):
   * `publish-templates`: required reviewers = release maintainers, enable "Prevent self-review", **uncheck** "Allow administrators to bypass configured protection rules"; deployment branches and tags = "Selected branches and tags" with a single **branch** rule `master` (no tag rules).
   * `dockerhub-publish`: the same settings.
   * Required reviewers must include at least two people. With self-review blocked, the person who merges or dispatches cannot approve their own run.
2. **Close the path to master that skips review** (Settings → Actions → General → Workflow permissions):
   * **Uncheck** "Allow GitHub Actions to create and approve pull requests". Otherwise any writer's workflow can approve their own PR with `GITHUB_TOKEN` and merge to master without human review, which defeats the master-only gate. Consider also enabling "Require approval of the most recent reviewable push" and "Do not allow bypassing the above settings" on master.
   * Any token stored as a repo-level secret can be read by a workflow on any branch. Check the other repo secrets, `GRAPHISTRY_GHA_CI_BUILD_GAK` and `GRAPHISTRY_GHA_CI_GAK`, which no workflow in this repo references. If either can approve or merge PRs here, or has other write access, delete it or move it to a protected environment.
3. **AWS OIDC provider**: in the bucket's AWS account, add the IAM identity provider `token.actions.githubusercontent.com` with audience `sts.amazonaws.com` (skip this if it already exists).
4. **IAM role** (for example `graph-app-kit-publish-templates`):
   * Trust policy, limited to this repo's `publish-templates` environment:

     ```json
     {
       "Version": "2012-10-17",
       "Statement": [{
         "Effect": "Allow",
         "Principal": { "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com" },
         "Action": "sts:AssumeRoleWithWebIdentity",
         "Condition": {
           "StringEquals": {
             "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
             "token.actions.githubusercontent.com:sub": "repo:graphistry/graph-app-kit:environment:publish-templates"
           }
         }
       }]
     }
     ```

     Optional hardening, so the role no longer depends only on the environment's settings: if your AWS account supports STS condition keys for GitHub-specific claims, also require `"token.actions.githubusercontent.com:ref": "refs/heads/master"` and `"token.actions.githubusercontent.com:job_workflow_ref": "graphistry/graph-app-kit/.github/workflows/publish.yml@refs/heads/master"`. Check that the IAM policy editor accepts these keys. A condition on a claim STS doesn't provide fails closed, which shows up in step 6 as an AssumeRole error.
   * Permissions policy, limited to the template path:

     ```json
     {
       "Version": "2012-10-17",
       "Statement": [{
         "Effect": "Allow",
         "Action": "s3:PutObject",
         "Resource": "arn:aws:s3:::graph-app-kit-repo-public/templates/latest/*"
       }]
     }
     ```

5. **Wire up the environments**:
   * `publish-templates`: add the environment variable `AWS_S3_PUBLISH_ROLE_ARN` = the role ARN from step 4. Until it is set, publish runs fail closed at "Require OIDC role configuration".
   * `dockerhub-publish`: create a **new** DockerHub access token and store environment secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` (the new token). Any branch could reach the old token before this change, so don't move it; replace it.
6. **Merge, then verify**: the merge (or a manual dispatch from master) starts Publish. Approve it, check that the four `templates/latest/{core,neptune}/{graphistry,minimal}.yml` objects have a new LastModified time, and confirm the job log shows the assumed role. Verify the DockerHub path at the next real release (tag first, then dispatch). A test dispatch republishes the latest tag's `v<tag>-<cuda>` and `latest-<cuda>` images from current master.
7. **Retire the old credentials** (once the template publish in step 6 succeeds; do not wait for a DockerHub release):
   * In IAM, check the "last used" info for the access key behind `S3_AWS_ACCESS_KEY_ID` to make sure nothing else uses it. Then deactivate and delete it.
   * Delete the repo-level secrets `S3_AWS_ACCESS_KEY_ID`, `S3_AWS_SECRET_ACCESS_KEY`, `S3_AWS_REGION_PUBLIC`, `AWS_S3_BUCKET_PUBLIC`, `DOCKERHUB_TOKEN` and `DOCKERHUB_USERNAME`.
   * Set Settings → Actions → General → Workflow permissions to "Read repository contents and packages permissions". Do this only once every workflow on master declares its own `permissions:`, which is true after this change merges.
   * Revoke the old DockerHub token. Environment secrets take precedence over repo secrets with the same name, so the next real release, run on the new `dockerhub-publish` token, is the check that it works. If it fails, fix the environment secrets.

Templates are no longer republished automatically on a schedule. If `templates/latest/` drifts, for example after a manual bucket edit, dispatch Publish from master.
