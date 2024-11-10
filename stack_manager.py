import boto3
from datetime import datetime, timezone
import time
from botocore.exceptions import ClientError
import sys

class CloudFormationManager:
    def __init__(self, region=None):
        self.cfn = boto3.client('cloudformation', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)

    def print_stack_events(self, stack_name, start_time):
        """Print recent stack events."""
        try:
            response = self.cfn.describe_stack_events(StackName=stack_name)
            events = [event for event in response['StackEvents'] 
                     if event['Timestamp'] > start_time]
            
            for event in reversed(events):
                status = event.get('ResourceStatus', '')
                reason = event.get('ResourceStatusReason', '')
                resource_id = event.get('LogicalResourceId', '')
                
                if ('FAILED' in status or reason or 
                    resource_id == stack_name or 
                    'IN_PROGRESS' not in status):
                    timestamp = event['Timestamp'].strftime('%H:%M:%S')
                    print(f"{timestamp} - {resource_id}: {status} {reason}")
                
        except Exception as e:
            print(f"Error getting stack events: {str(e)}")

    def wait_for_stack(self, stack_name, operation='create'):
        """Wait for stack operation to complete with enhanced monitoring."""
        print(f"Waiting for stack {operation} to complete...")
        start_time = datetime.now(timezone.utc)
        
        try:
            while True:
                try:
                    response = self.cfn.describe_stacks(StackName=stack_name)
                    stack = response['Stacks'][0]
                    status = stack['StackStatus']
                    
                    self.print_stack_events(stack_name, start_time)
                    
                    if 'ROLLBACK' in status and status != 'UPDATE_ROLLBACK_COMPLETE':
                        raise Exception(f"Stack {operation} failed: {status}")
                    
                    if status.endswith('COMPLETE'):
                        if status.startswith(operation.upper()):
                            print(f"Stack {operation} completed successfully")
                            return
                        else:
                            raise Exception(f"Stack {operation} failed: {status}")
                    
                    time.sleep(5)
                    
                except ClientError as e:
                    if 'does not exist' in str(e):
                        time.sleep(5)
                        continue
                    raise
                
        except Exception as e:
            print(f"Error during stack {operation}: {str(e)}")
            self.print_stack_events(stack_name, start_time)
            sys.exit(1)

    def deploy_stack(self, stack_name, template_body, parameters=None):
        """Deploy or update CloudFormation stack with enhanced error handling."""
        try:
            params = {
                'StackName': stack_name,
                'TemplateBody': template_body,
                'Capabilities': ['CAPABILITY_IAM']
            }
            if parameters:
                params['Parameters'] = parameters

            try:
                stack = self.cfn.describe_stacks(StackName=stack_name)
                print(f"Updating stack: {stack_name}")
                try:
                    self.cfn.update_stack(**params)
                    self.wait_for_stack(stack_name, 'update')
                except ClientError as e:
                    if 'No updates are to be performed' in str(e):
                        print("No infrastructure changes needed, updating function code...")
                        # Get the function name from the stack outputs
                        function_name = None
                        for output in stack['Stacks'][0]['Outputs']:
                            if output['OutputKey'] == 'LambdaArn':
                                function_name = output['OutputValue'].split(':')[-1]
                                break
                        
                        if function_name:
                            # Force update of the function code
                            for param in parameters:
                                if param['ParameterKey'] == 'ImageUri':
                                    image_uri = param['ParameterValue']
                                    print(f"Updating Lambda function code with new image: {image_uri}")
                                    self.lambda_client.update_function_code(
                                        FunctionName=function_name,
                                        ImageUri=image_uri,
                                        Publish=True
                                    )
                                    break
                    else:
                        raise
            except ClientError as e:
                if 'does not exist' in str(e):
                    print(f"Creating stack: {stack_name}")
                    self.cfn.create_stack(**params)
                    self.wait_for_stack(stack_name, 'create')
                else:
                    raise
            
        except Exception as e:
            print(f"Error deploying CloudFormation stack: {str(e)}")
            sys.exit(1)

    def delete_stack(self, stack_name):
        """Delete a CloudFormation stack."""
        try:
            print(f"Deleting stack: {stack_name}")
            self.cfn.delete_stack(StackName=stack_name)
            self.wait_for_stack(stack_name, 'delete')
        except ClientError as e:
            if 'does not exist' not in str(e):
                raise

    def get_stack_outputs(self, stack_name):
        """Get outputs from a CloudFormation stack."""
        response = self.cfn.describe_stacks(StackName=stack_name)
        return {output['OutputKey']: output['OutputValue'] 
                for output in response['Stacks'][0]['Outputs']}
