from aws_cdk import Stack, aws_s3 as s3, RemovalPolicy, Tags

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

        # apply tag to the staging bucket
        Tags.of(staging_bucket).add("Bucket", "Staging")

        # prod bucket
        prod_bucket = s3.Bucket(self, "ProdWebsiteBucket",
                                bucket_name="prod-website-bucket",
                                versioned=False,
                                removal_policy=RemovalPolicy.DESTROY,
                                website_index_document="index.html",
                                website_error_document="error.html",
                                public_read_access=True
                                )
        # apply tag to the production bucket
        Tags.of(prod_bucket).add("Bucket", "Production")
