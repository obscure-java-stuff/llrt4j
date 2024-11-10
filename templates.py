def get_infrastructure_template(repository_name):
    """Generate CloudFormation template for ECR and IAM resources."""
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "Infrastructure for Docker-based Lambda function (ECR and IAM)",
        "Resources": {
            "LambdaExecutionRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": ["lambda.amazonaws.com"]
                                },
                                "Action": ["sts:AssumeRole"]
                            }
                        ]
                    },
                    "ManagedPolicyArns": [
                        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    ],
                    "Path": "/"
                }
            },
            "ECRRepository": {
                "Type": "AWS::ECR::Repository",
                "Properties": {
                    "RepositoryName": repository_name,
                    "ImageScanningConfiguration": {
                        "ScanOnPush": True
                    },
                    "ImageTagMutability": "MUTABLE"
                }
            }
        },
        "Outputs": {
            "RoleArn": {
                "Description": "ARN of the Lambda execution role",
                "Value": {
                    "Fn::GetAtt": ["LambdaExecutionRole", "Arn"]
                }
            },
            "RepositoryUri": {
                "Description": "URI of the ECR repository",
                "Value": {
                    "Fn::GetAtt": ["ECRRepository", "RepositoryUri"]
                }
            }
        }
    }

def get_lambda_template(function_name):
    """Generate CloudFormation template for Lambda function."""
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "Lambda function using Docker image",
        "Parameters": {
            "RoleArn": {
                "Type": "String",
                "Description": "ARN of the Lambda execution role"
            },
            "ImageUri": {
                "Type": "String",
                "Description": "URI of the Docker image in ECR"
            }
        },
        "Resources": {
            "LambdaFunction": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "FunctionName": function_name,
                    "PackageType": "Image",
                    "Code": {
                        "ImageUri": {"Ref": "ImageUri"}
                    },
                    "Role": {"Ref": "RoleArn"},
                    "Timeout": 30,
                    "MemorySize": 2048
                }
            }
        },
        "Outputs": {
            "LambdaArn": {
                "Description": "ARN of the Lambda function",
                "Value": {
                    "Fn::GetAtt": ["LambdaFunction", "Arn"]
                }
            }
        }
    }