import json
import os
from pathlib import Path

from aws_cdk import (Stack, aws_s3 as s3, RemovalPolicy, Tags, aws_codepipeline as codepipeline,
                     aws_codepipeline_actions as codepipeline_actions,
                     aws_iam as iam, )

from constructs import Construct


class S3PipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

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
                                block_public_access=s3.BlockPublicAccess(block_public_acls=False)
                                )

        # apply tag to the production bucket
        Tags.of(prod_bucket).add("Bucket", "Production")

        # load policy for codepipeline
        base_dir = Path(__file__).resolve().parent.parent
        policy_file_path = base_dir / "policies/codepipeline_policy.json"

        # open policy
        with open(policy_file_path) as f:
            policy_document = json.load(f)

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
            statements=[iam.PolicyStatement.from_json(statement) for statement in policy_document['Statement']],
            roles=[pipeline_role]
        )

        # source action for CodePipeline
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.S3SourceAction(
            action_name="S3Source",
            bucket=staging_bucket,
            bucket_key="src.zip",
            output=source_output,
            variables_namespace="PipelineSourceVariables"
        )

        # deploy action for CodePipeline
        deploy_action = codepipeline_actions.S3DeployAction(
            action_name="S3Deploy",
            bucket=prod_bucket,
            input=source_output,
            extract=True,
            variables_namespace='PipelineDeployVariables',
            access_control=s3.BucketAccessControl.PUBLIC_READ

        )
