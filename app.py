#!/usr/bin/env python3
import os

import aws_cdk as cdk

from s3_pipeline.s3_pipeline_stack import S3PipelineStack


app = cdk.App()
S3PipelineStack(
    app,
    "S3PipelineStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

app.synth()
