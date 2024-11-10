import boto3
import docker
import base64
import sys

class DockerManager:
    def __init__(self, region=None):
        self.ecr = boto3.client('ecr', region_name=region)
        self.docker_client = docker.from_env()

    def get_ecr_credentials(self):
        """Get ECR login credentials."""
        try:
            token = self.ecr.get_authorization_token()
            username, password = base64.b64decode(
                token['authorizationData'][0]['authorizationToken']
            ).decode().split(':')
            return username, password, token['authorizationData'][0]['proxyEndpoint']
        except Exception as e:
            print(f"Error getting ECR credentials: {str(e)}")
            sys.exit(1)

    def push_image(self, source_image, repository_uri):
        """Push Docker image to ECR."""
        try:
            # Get ECR credentials and login
            username, password, registry = self.get_ecr_credentials()
            self.docker_client.login(
                username=username,
                password=password,
                registry=registry.replace('https://', '')
            )

            # Build the image with platform specification
            print(f"Building image: {source_image}")
            image, logs = self.docker_client.images.build(
                path=".",
                dockerfile="Dockerfile",
                tag=source_image,
                platform="linux/amd64",
                labels={
                    "lambda.runtime-api.version": "0.1"
                }
            )
            
            # Tag and push the image
            image.tag(repository_uri, 'latest')
            
            print("Pushing image to ECR...")
            for line in self.docker_client.images.push(repository_uri, 'latest', stream=True, decode=True):
                if 'status' in line:
                    print(line['status'])
                if 'error' in line:
                    raise Exception(line['error'])
            
            print("Image pushed successfully")
            
        except Exception as e:
            print(f"Error pushing Docker image: {str(e)}")
            sys.exit(1)
