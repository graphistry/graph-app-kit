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

## DockerHub Automated Builds

Managed via DockerHub automates tagged builds

Ahead of time:

* Ensure you've set `GRAPHISTRY_FORGE_BASE_VERSION` in the `Dockerfile` (not just the `docker-compose.yml`)
* Merged into master

Publish:

1. `git tag 2.39.12`
  * Use a tag that corresponds to the Graphistry version, or some suffix (`2.39.12.1`)
  * Note lack of `v`
2. `git push --tags`

DockerHub automatic builds will:
* publish as tag `v2.39.12-11.4`: note addition of `v` and `-11.4`
* publish as tag `latest`

See [current tags](https://hub.docker.com/r/graphistry/graph-app-kit-st/tags) and available [base tags](https://hub.docker.com/r/graphistry/graphistry-forge-base/tags)

## DockerHub publish action

`.github/workflows/dockerhubpublish.yml` builds and pushes `graphistry/graph-app-kit-st` on a release tag push, or by manual dispatch **from master or a tag**. Dispatches from other branches are skipped. The job runs in the `dockerhub-publish` GitHub environment, which holds the `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` secrets.

## AWS Publish action

`.github/workflows/publish.yml` uploads the CloudFormation templates (`src/bootstraps/{core,neptune}/{graphistry,minimal}.yml`) to `s3://graph-app-kit-repo-public/templates/latest/`. The README "Launch Stack" buttons point at that path, so it is what customers deploy.

* Runs on merge to `master` when a template (or the workflow) changes, or by manual dispatch **from master**. Other refs are skipped, and PR labels no longer publish.
* Every run waits in the `publish-templates` environment for a required reviewer to approve.
* AWS access uses GitHub OIDC. No AWS keys are stored in GitHub.

To test template changes before merge, upload your branch's template by hand to CloudFormation (see "Test / AWS" above). Don't publish it to `templates/latest/`.

### One-time setup (repo admin + AWS admin)

1. **AWS OIDC provider**: in the bucket's AWS account, add the IAM identity provider `token.actions.githubusercontent.com` with audience `sts.amazonaws.com` (skip this if it already exists).
2. **IAM role** (for example `graph-app-kit-publish-templates`):
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

3. **GitHub environment `publish-templates`** (Settings → Environments):
   * Required reviewers: the release maintainers. Enable "Prevent self-review".
   * Deployment branches and tags: "Selected branches", with only `master`.
   * Environment variable `AWS_S3_PUBLISH_ROLE_ARN` = the role ARN from step 2.
4. **GitHub environment `dockerhub-publish`**: deployment branches and tags = `master` plus the release tag pattern (for example `[0-9]*`). Optionally add required reviewers. Move `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` here as environment secrets, then delete the repo-level copies.
5. **Retire the old credentials**: deactivate and delete the IAM access key behind `S3_AWS_ACCESS_KEY_ID`. Then delete the repo secrets `S3_AWS_ACCESS_KEY_ID`, `S3_AWS_SECRET_ACCESS_KEY`, `S3_AWS_REGION_PUBLIC` and `AWS_S3_BUCKET_PUBLIC`. Rotate the DockerHub token, since any branch could previously reach it.
