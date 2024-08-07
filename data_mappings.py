import boto3
import json
from concurrent.futures import ThreadPoolExecutor


# SETUP VARIABLES
session = boto3.Session(profile_name='#SOURCE_AWS_PROFILE#') #Replace with AWS CLI Profile name
identity_store_id = '#SOURCE_IDENTITY_STORE_ID#'  # Replace with target IAM Identity Center Identity Store ID
identity_store_arn = '#SOURCE_IDENTITY_STORE_ARN#'  # Replace with your Identity Store ARN
identitystore_client = session.client('identitystore')


# GET GROUPS DATA
def get_all_groups(identitystore_client, identity_store_id):
    print('Colleting groups data...')
    groups = []
    paginator = identitystore_client.get_paginator('list_groups')
    pages = paginator.paginate(IdentityStoreId=identity_store_id)
    for page in pages:
        for group in page['Groups']:
            groups.append({
                'GroupId': group['GroupId'],
                'DisplayName': group['DisplayName'],
                'Description': group.get('Description', '')
            })
    return groups


# GET USER DATA
def get_all_users(identitystore_client, identity_store_id):
    print('Collecting users data...')
    users = []
    paginator = identitystore_client.get_paginator('list_users')
    pages = paginator.paginate(IdentityStoreId=identity_store_id)
    for page in pages:
        for user in page['Users']:
            users.append({
                'Info': user
            })
    return users


# GET USER TO GROUP MAPPING
def get_user_group_memberships(identitystore_client, groups, identity_store_id):
    print('Collecting user to group mapping...')
    user_group_memberships = []
    user_group_mapping = {}
    paginator = identitystore_client.get_paginator('list_group_memberships')
    pages = paginator.paginate(IdentityStoreId=identity_store_id, GroupId=groups)
    for page in pages:
        for membership in page.get('GroupMemberships', []):
            group_id = membership['GroupId']
            user_id = membership['MemberId']['UserId']
            if group_id in user_group_mapping:
                user_group_mapping[group_id].append(user_id)
            else:
                user_group_mapping[group_id] = [user_id]
    formatted_output = []
    for group_id, user_ids in user_group_mapping.items():
        formatted_output.append({
            'GroupId': group_id,
            'UserIds': user_ids
        })
    return user_group_memberships


# CORRELATES GROUP IDS AND USER IDS TO GROUPS NAMES AND USER NAMES
def get_user_group_memberships(identitystore_client, group_id, identity_store_id):

    user_group_mapping = []
    paginator = identitystore_client.get_paginator('list_group_memberships')
    pages = paginator.paginate(IdentityStoreId=identity_store_id, GroupId=group_id)

    for page in pages:
        for membership in page.get('GroupMemberships', []):
            user_id = membership['MemberId']['UserId']
            user_group_mapping.append({
                'GroupId': group_id,
                'UserId': user_id
            })

    return user_group_mapping

users = get_all_users(identitystore_client, identity_store_id)
groups = get_all_groups(identitystore_client, identity_store_id)
group_map = {group['GroupId']: group['DisplayName'] for group in groups}
user_group_mapping = []
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(get_user_group_memberships, identitystore_client, group['GroupId'], identity_store_id) for group in groups]
    for user in users:
        user_groups = []
        for future in futures:
            user_group_memberships = future.result()
            for membership in user_group_memberships:
                if membership['UserId'] == user['Info']['UserId']:
                    user_groups.append({
                        group_map[membership['GroupId']]
                    })
        user_group_mapping.append({
            'UserName': user['Info']['UserName'],
            'Groups': user_groups
        })


# CONVERT PYTHON SETS INTO LISTS
def convert_sets_to_lists(user_group_mapping):
    if isinstance(user_group_mapping, set):
        return list(user_group_mapping)
    elif isinstance(user_group_mapping, dict):
        return {k: convert_sets_to_lists(v) for k, v in user_group_mapping.items()}
    elif isinstance(user_group_mapping, list):
        return [convert_sets_to_lists(item) for item in user_group_mapping]
    return user_group_mapping


def convert_sets_to_lists(groups):
    if isinstance(groups, set):
        return list(groups)
    elif isinstance(groups, dict):
        return {k: convert_sets_to_lists(v) for k, v in groups.items()}
    elif isinstance(groups, list):
        return [convert_sets_to_lists(item) for item in groups]
    return groups


def convert_sets_to_lists(users):
    if isinstance(users, set):
        return list(users)
    elif isinstance(users, dict):
        return {k: convert_sets_to_lists(v) for k, v in users.items()}
    elif isinstance(users, list):
        return [convert_sets_to_lists(item) for item in users]
    return users


user_group_mapping_serializable = convert_sets_to_lists(user_group_mapping)
groups_serializable = convert_sets_to_lists(groups)
users_serializable = convert_sets_to_lists(users)

#JSON SERIALIZATION
mapping_json_data = json.dumps(user_group_mapping_serializable, indent=2)
with open('mappings/user_to_group_mapping.json', 'w') as f:
    f.write(mapping_json_data)

groups_json_data = json.dumps(groups_serializable, indent=2)
with open('mappings/groups_data.json', 'w') as f:
    f.write(groups_json_data)

users_json_data = json.dumps(users_serializable, indent=2)
with open('mappings/users_data.json', 'w') as f:
    f.write(users_json_data)


#BACKUP PERMISSION SETS
sso_admin_client = session.client('sso-admin')
def list_permission_sets(identity_store_arn):
    try:
        print('Collecting permission sets and its correlations to groups and AWS Accounts...')
        response = sso_admin_client.list_permission_sets(
            InstanceArn=identity_store_arn
        )

        permission_sets = response['PermissionSets']

        return permission_sets
    
    except Exception as e:
        print(f"Error listing permission sets: {str(e)}")
        return []


#DESCRIBES PERMISSION SETS
def describe_permission_set(identity_store_arn, permission_set_arn):
    try:

        response = sso_admin_client.describe_permission_set(
            InstanceArn=identity_store_arn,
            PermissionSetArn=permission_set_arn
        )

        permission_set_info = response['PermissionSet']

        return permission_set_info
    
    except Exception as e:
        print(f"Error describing permission set {permission_set_arn}: {str(e)}")
        return None


#GATHER ACCOUNTS WITHIN EACH PERMISSION SET
def list_accounts_for_permission_set(identity_store_arn, permission_set_arn):

    try:

        response = sso_admin_client.list_accounts_for_provisioned_permission_set(
            InstanceArn=identity_store_arn,
            PermissionSetArn=permission_set_arn
        )

        accounts = response['AccountIds']
        return accounts
    
    except Exception as e:
        print(f"Error listing accounts for permission set {permission_set_arn}: {str(e)}")
        return []


#GATHER AWS, CUSTOMER AND INLINE POLICIES
def list_attached_policies(permission_set_arn):
    try:

        response_managed = sso_admin_client.list_managed_policies_in_permission_set(
            InstanceArn=identity_store_arn,
            PermissionSetArn=permission_set_arn
        )
        managed_policies = response_managed.get('AttachedManagedPolicies', [])

        response_customer = sso_admin_client.list_customer_managed_policy_references_in_permission_set(
            InstanceArn=identity_store_arn,
            PermissionSetArn=permission_set_arn
        )
        customer_managed_policies = response_customer.get('AttachedPolicies', [])
        
        response_inline = sso_admin_client.get_inline_policy_for_permission_set(
            InstanceArn=identity_store_arn,
            PermissionSetArn=permission_set_arn
        )

        inline_policies = response_inline.get('AttachedPolicies', [])
        attached_policies = managed_policies + customer_managed_policies + inline_policies

        return attached_policies
    
    except Exception as e:
        print(f"Error listing attached policies for permission set {permission_set_arn}: {str(e)}")
        return []


#BACKUP OUTPUT INTO MAPPINGS FOLDER
def backup_permission_sets_details(identity_store_arn, output_file):
    try:
        print("Writing files...")
        permission_sets = list_permission_sets(identity_store_arn)

        if not permission_sets:
            print("No permission sets found.")
            return

        detailed_permission_sets = []

        for permission_set_arn in permission_sets:
            permission_set_info = describe_permission_set(identity_store_arn, permission_set_arn)
    
            if permission_set_info:
                accounts = list_accounts_for_permission_set(identity_store_arn, permission_set_arn)
                attached_policies = list_attached_policies(permission_set_arn)
                
                detailed_permission_set = {
                    'PermissionSetName': permission_set_info['Name'],
                    'Description': permission_set_info.get('Description', ''),
                    'SessionDuration': permission_set_info['SessionDuration'],
                    'Accounts': accounts,
                    'AttachedPolicies': attached_policies
                }

                detailed_permission_sets.append(detailed_permission_set)
            else:
                print(f"Permission set info not found for {permission_set_arn}")
        
        print("Finishing up....") 
        permission_sets_data = {
            'IdentityStoreId': identity_store_arn,
            'PermissionSets': detailed_permission_sets
        }
        
        with open(output_file, 'w') as f:
            json.dump(permission_sets_data, f, indent=2)
        
        print(f"Done!")

    except Exception as e:
        print(f"Error backing up permission sets details: {str(e)}")

# EXAMPLE USAGE:
if __name__ == '__main__':
    output_file = 'mappings/permission_sets_data.json'

    backup_permission_sets_details(identity_store_arn, output_file)