"""This is the main program for CDK entry"""

# !/usr/bin/env python3
import os
import sys

from aws_cdk import core

from swift_main_stack.main import SwiftMain

region = os.environ["CDK_DEFAULT_REGION"]
account = os.environ["CDK_DEFAULT_ACCOUNT"]

if region == "" or account == "":
    print("Please set CDK_DEFAULT_REGION and CDK_DEFAULT_ACCOUNT in Env!")
    sys.exit()

environment = core.Environment(region=region, account=account)

app = core.App()
main_stack = SwiftMain(app, "SWIFTMain-" + region, env=environment,
                       description="Quick Start for SWIFT Connectivity (qs-1rlbqnpbe)")

app.synth()
