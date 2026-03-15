import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Desired state from Terraform (hardcoded – this is what we enforce)
DESIRED_EC2_TAGS = {
    'Name': 'Drift-Demo-EC2',
    'Environment': 'prod',
    'ManagedBy': 'Terraform'
}

DESIRED_SG_RULES = [
    {
        'IpProtocol': 'tcp',
        'FromPort': 22,
        'ToPort': 22,
        'CidrIp': '0.0.0.0/0'   # Change to your IP in production
    }
]

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    logger.info("=== Drift Detection Started ===")
    
    # 1. Check EC2 tags
    instances = ec2.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': ['Drift-Demo-EC2']}])
    instance_id = instances['Reservations'][0]['Instances'][0]['InstanceId']
    
    current_tags = {tag['Key']: tag['Value'] for tag in instances['Reservations'][0]['Instances'][0].get('Tags', [])}
    
    if current_tags.get('Environment') != 'prod':
        logger.warning(f"Drift detected on EC2 {instance_id}! Restoring tags...")
        ec2.create_tags(Resources=[instance_id], Tags=[{'Key': k, 'Value': v} for k, v in DESIRED_EC2_TAGS.items()])
        logger.info("EC2 tags restored ✅")
    
    # 2. Check Security Group rules
    sg = ec2.describe_security_groups(GroupNames=['drift-sg'])
    current_rules = sg['SecurityGroups'][0]['IpPermissions']
    
    # Simple check: if SSH rule is missing or extra rules exist
    has_drift = len(current_rules) != 1 or current_rules[0].get('FromPort') != 22
    
    if has_drift:
        logger.warning("Drift detected in Security Group! Restoring rules...")
        # Remove all existing rules
        for rule in current_rules:
            ec2.revoke_security_group_ingress(GroupName='drift-sg', IpPermissions=[rule])
        # Add correct rule
        ec2.authorize_security_group_ingress(
            GroupName='drift-sg',
            IpPermissions=DESIRED_SG_RULES
        )
        logger.info("Security Group restored ✅")
    
    logger.info("=== Drift check completed ===")
    return {"status": "success", "message": "Drift detection & remediation finished"}