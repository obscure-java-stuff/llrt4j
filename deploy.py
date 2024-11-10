import boto3
import argparse
import time
import os
import json
from templates import get_infrastructure_template, get_lambda_template
from stack_manager import CloudFormationManager
from docker_manager import DockerManager

class LambdaDeployer:
    def __init__(self, docker_image, function_name=None, repository_name=None, stack_name=None):
        # Get AWS region
        self.session = boto3.session.Session()
        self.region = self.session.region_name or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Get account ID
        self.sts = boto3.client('sts')
        self.account_id = self.sts.get_caller_identity()["Account"]
        
        # Initialize managers
        self.cfn_manager = CloudFormationManager(self.region)
        self.docker_manager = DockerManager(self.region)
        
        # Set parameters
        self.docker_image = docker_image
        self.function_name = function_name or 'TestFunction'
        self.repository_name = repository_name or self.function_name.lower()
        self.stack_name = stack_name or f"lambda-docker-stack-{self.function_name.lower()}"
        
        # Set ECR repository URI
        self.repository_uri = f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{self.repository_name}"
        
        print(f"Configured deployment:")
        print(f"Region: {self.region}")
        print(f"Account ID: {self.account_id}")
        print(f"Stack Name: {self.stack_name}")
        print(f"Repository: {self.repository_name}")
        print(f"Function: {self.function_name}")

    def deploy(self):
        """Run the complete deployment process."""
        try:
            print("Starting deployment process...")
            
            # Deploy infrastructure stack
            infra_stack_name = f"{self.stack_name}-infra"
            print("Deploying infrastructure stack...")
            
            # Convert template to JSON string with proper handling of boolean values
            infra_template = json.dumps(
                get_infrastructure_template(self.repository_name),
                indent=2
            ).replace('True', 'true').replace('False', 'false')
            
            self.cfn_manager.deploy_stack(infra_stack_name, infra_template)
            
            # Get infrastructure outputs
            infra_outputs = self.cfn_manager.get_stack_outputs(infra_stack_name)
            role_arn = infra_outputs['RoleArn']
            
            # Push Docker image
            print("Pushing Docker image...")
            self.docker_manager.push_image(self.docker_image, self.repository_uri)
            
            # Wait for image to be available
            print("Waiting for image to be available in ECR...")
            time.sleep(10)
            
            # Deploy Lambda function
            lambda_stack_name = f"{self.stack_name}-function"
            print("Deploying Lambda function stack...")
            
            # Convert template to JSON string
            lambda_template = json.dumps(
                get_lambda_template(self.function_name),
                indent=2
            ).replace('True', 'true').replace('False', 'false')
            
            lambda_parameters = [
                {'ParameterKey': 'RoleArn', 'ParameterValue': role_arn},
                {'ParameterKey': 'ImageUri', 'ParameterValue': f"{self.repository_uri}:latest"}
            ]
            self.cfn_manager.deploy_stack(lambda_stack_name, lambda_template, lambda_parameters)
            
            print("Deployment completed successfully!")
            
        except Exception as e:
            print(f"Deployment failed: {str(e)}")
            sys.exit(1)

    def cleanup(self):
        """Clean up all resources."""
        try:
            # Delete Lambda function stack
            lambda_stack_name = f"{self.stack_name}-function"
            self.cfn_manager.delete_stack(lambda_stack_name)
            
            # Delete infrastructure stack
            infra_stack_name = f"{self.stack_name}-infra"
            self.cfn_manager.delete_stack(infra_stack_name)
            
            print("Cleanup completed successfully!")
            
        except Exception as e:
            print(f"Cleanup failed: {str(e)}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Deploy Docker image to AWS Lambda via ECR using CloudFormation'
    )
    parser.add_argument('--docker-image', required=True, help='Local Docker image name:tag')
    parser.add_argument('--function-name', help='Lambda function name (default: TestFunction)')
    parser.add_argument('--repository-name', help='ECR repository name (defaults to function name)')
    parser.add_argument('--stack-name', help='CloudFormation stack name')
    parser.add_argument('--cleanup', action='store_true', help='Clean up all resources')

    args = parser.parse_args()

    deployer = LambdaDeployer(
        docker_image=args.docker_image,
        function_name=args.function_name,
        repository_name=args.repository_name,
        stack_name=args.stack_name
    )
    
    if args.cleanup:
        deployer.cleanup()
    else:
        deployer.deploy()

if __name__ == '__main__':
    main()
