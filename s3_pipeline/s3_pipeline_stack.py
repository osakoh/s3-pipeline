import json
import os
from pathlib import Path

from aws_cdk import (Stack, aws_s3 as s3, RemovalPolicy, Tags, aws_codepipeline as codepipeline,
                     aws_codepipeline_actions as codepipeline_actions,
                     aws_iam as iam, CfnOutput, )

from constructs import Construct


class S3PipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # policy folder path
        base_dir = Path(__file__).resolve().parent.parent

        # source bucket
        staging_bucket = s3.Bucket(
            self,
            "StagingWebsiteBucket",
            bucket_name="001-staging-website-bucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # apply tag to the staging bucket
        Tags.of(staging_bucket).add("Bucket", "Staging")

        # prod bucket
        prod_bucket = s3.Bucket(self, "ProdWebsiteBucket",
                                bucket_name="001-prod-website-bucket",
                                removal_policy=RemovalPolicy.DESTROY,
                                website_index_document="index.html",
                                website_error_document="error.html",
                                versioned=True,
                                block_public_access=s3.BlockPublicAccess(block_public_policy=False),
                                # access_control=s3.BucketAccessControl.PUBLIC_READ
                                )

        # load bucket policy
        bucket_policy_file_path = base_dir / "policies/bucket_policy.json"

        # open policy
        with open(bucket_policy_file_path) as f:
            bucket_policy = json.load(f)

        # modify the policy's Resource to match the actual bucket ARN if necessary
        bucket_policy['Statement'][0]['Resource'] = f"{prod_bucket.bucket_arn}/*"

        # Apply the loaded policy to the production bucket
        for statement in bucket_policy['Statement']:
            prod_bucket.add_to_resource_policy(iam.PolicyStatement.from_json(statement))

        # apply tag to the production bucket
        Tags.of(prod_bucket).add("Bucket", "Production")

        # output for the prod_bucket Static Website Hosting URL
        CfnOutput(
            self, "ProdBucketWebsiteURL",
            value=f"http://{prod_bucket.bucket_name}.s3-website-{self.region}.amazonaws.com",
            description="URL for the production static website"
        )

        # load policy for codepipeline
        base_dir = Path(__file__).resolve().parent.parent
        pipeline_policy_file_path = base_dir / "policies/codepipeline_policy.json"

        # open policy
        with open(pipeline_policy_file_path) as f:
            pipeline_policy = json.load(f)

        # create IAM role for codepipeline
        pipeline_role = iam.Role(
            self, "CodePipelineRole",
            assumed_by=iam.ServicePrincipal("codepipeline.amazonaws.com")
        )

        # create IAM policy using the statements loaded from the JSON file
        # attach policy to role
        policy = iam.Policy(
            self, "PipelinePolicy",
            policy_name="S3PipelinePolicy",
            statements=[iam.PolicyStatement.from_json(statement) for statement in pipeline_policy['Statement']],
            roles=[pipeline_role]
        )

        # source action for CodePipeline
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.S3SourceAction(
            action_name="S3Source",
            bucket=staging_bucket,
            bucket_key="src.zip",
            output=source_output,
            trigger=codepipeline_actions.S3Trigger.EVENTS,
            variables_namespace="PipelineSourceVariables"
        )

        # deploy action for CodePipeline
        deploy_action = codepipeline_actions.S3DeployAction(
            action_name="S3Deploy",
            bucket=prod_bucket,
            input=source_output,
            extract=True,
            variables_namespace='PipelineDeployVariables',
            # access_control=s3.BucketAccessControl.PUBLIC_READ

        )

        # create pipeline
        pipeline = codepipeline.Pipeline(
            self, "DeploymentPipeline",
            pipeline_name="DeploymentPipeline",
            role=pipeline_role,
            stages=[
                codepipeline.StageProps(stage_name="Source", actions=[source_action]),
                codepipeline.StageProps(stage_name="Deploy", actions=[deploy_action])
            ])

        # tag pipeline
        Tags.of(pipeline).add("Project", "Production Pipeline")
