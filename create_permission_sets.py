import json
import boto3


#CREATE PERMISSIONS SETS BASED ON MAPPED DATA
def create_identity_center_groups(file_path):
    # Create a session using your AWS credentials
    session = boto3.Session(profile_name='#DESTINATION_AWS_PROFILE#') #Replace with AWS CLI Profile name

    # IAM Identity Center instance details
    identity_store_arn = '#DESTINATION_IDENTITY_STORE_ID#'  # Replace with your Identity Store ARN
    # Create a client for the Identity Store
    sso_admin_client = session.client('sso-admin')
    
    # Read permission set data from JSON file
    with open(file_path, 'r') as f:
        permission_sets_data = json.load(f)
    
    with open('./mappings/new_groups_data.json') as f:
        new_groups_data = json.load(f)

    # Iterate over each group data and create groups in Identity Center
    DEFAULT_SESSION_DURATION = 'PT4H'
    DEFAULT_DESCRIPTION = 'Custom permission set'
    for permission_set_data in permission_sets_data['PermissionSets']:
        display_name = permission_set_data.get('PermissionSetName')
        if 'Description' in permission_set_data:
            description = permission_set_data['Description']
            if len(description) == 0:
                description = DEFAULT_DESCRIPTION
        else:
            description = DEFAULT_DESCRIPTION

        if 'SessionDuration' in permission_set_data:
            session_duration = permission_set_data['SessionDuration']
            if len(session_duration) == 0:
                session_duration = DEFAULT_SESSION_DURATION
        else:
            session_duration = DEFAULT_DESCRIPTION
        if 'Accounts' in permission_set_data: aws_account_ids = permission_set_data['Accounts']
        else: 
            print('No AWS accounts mapped')

        try:
            response = sso_admin_client.create_permission_set(
                InstanceArn=identity_store_arn,
                Name=display_name,
                Description=description,
                SessionDuration=session_duration
            )
            print(f"Successfully created permission set: {display_name}")
            permission_set_arn = response['PermissionSet']['PermissionSetArn']
            print(permission_set_arn)

            # Find the corresponding group ID in the new groups data
            group_data = next((group for group in new_groups_data for key, value in group.items() if key == display_name), None)


            if group_data:
                group_id = list(group_data.values())[0]

                # Use the permission_set_arn to map the AWS accounts
                for aws_account_id in aws_account_ids:
                    sso_admin_client.create_account_assignment(
                        InstanceArn=identity_store_arn,
                        TargetId=aws_account_id,
                        TargetType='AWS_ACCOUNT',
                        PermissionSetArn=permission_set_arn,
                        PrincipalType='GROUP',
                        PrincipalId=group_id
                    )
                    print(f"Successfully added account: {aws_account_id} to permission set '{display_name}' for group '{group_id}'")
            else:
                print(f"Group not found for permission set '{display_name}'")

        except sso_admin_client.exceptions.ValidationException as e:
            print(f"ValidationException: {e}")
        except sso_admin_client.exceptions.InternalServerException as e:
            print(f"InternalServerException: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
#ATTACH EXISTING POLICIES TO CREATED PERMISSION SETS
        attached_policies = permission_set_data['AttachedPolicies']
        for policy_info in attached_policies:
            policy_arn = policy_info.get('Arn')
            if policy_arn:
                try:
                    response = sso_admin_client.attach_managed_policy_to_permission_set(
                        InstanceArn=identity_store_arn,
                        ManagedPolicyArn=policy_arn,
                        PermissionSetArn=permission_set_arn
                    )
                    print(f"Successfully attached policy: {policy_arn}")
                except sso_admin_client.exceptions.ConflictException as e:
                    print(f"Unable to attach policy {policy_arn}: {e}")
                except Exception as e:
                    print(f"Unexpected error while attaching policy {policy_arn}: {e}")
            else:
                print(f"Skipping invalid policy: {policy_info}")

#EXAMPLE USAGE:
if __name__ == '__main__':
    file_path = 'mappings/permission_sets_data.json'
    create_identity_center_groups(file_path)
