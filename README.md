
# SWIFT CSP QuickStart  

This is a quick start project for the reference architecture for the connectivity to SWIFT (https://www.swift.com/)

This project is based on AWS Cloud Development Kit (AWS CDK) developed in Python 
https://docs.aws.amazon.com/cdk/latest/guide/work-with-cdk-python.html


![Architecture](./docs/images/figure1.png)

Note:
- RHEL images do not have ssm-agent installed by default
- By default this deployment does NOT include RDS Oracle; modify the skip_oracle flag in cdk.json to install
- Choose any RHEL 7.9 or 8.2 AMI to use in cdk.json (please refer to Swift OS requirements)
