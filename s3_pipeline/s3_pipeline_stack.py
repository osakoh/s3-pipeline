from aws_cdk import Stack, aws_s3 as s3, RemovalPolicy, CfnTag, Tags

from constructs import Construct


class S3PipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # source bucket
        staging_bucket = s3.Bucket(
            self,
            "StagingWebsiteBucket",
            bucket_name="staging-website-bucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # apply tags to the staging bucket
        Tags.of(staging_bucket).add("Bucket", "Staging")


