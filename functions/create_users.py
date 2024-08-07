import json
import boto3

#CREATES USERS USING MAPPED DATA FROM SOURCE ACCOUNT
def create_identity_center_groups(file_path):
    session = boto3.Session(profile_name='#DESTINATION_AWS_PROFILE#')  # Replace with AWS CLI Profile name

    identity_store_id = '#DESTINATION_IDENTITY_STORE_ID#'  # Replace with target IAM Identity Center Identity Store ID

    identitystore_client = session.client('identitystore')
    
    with open('../mappings/users_data.json', 'r') as f:
        users_data = json.load(f)

    with open('../mappings/user_to_group_mapping.json', 'r') as f:
        user_group_mappings = json.load(f)

    with open('../mappings/new_groups_data.json', 'r') as f:
        group_name_id_mappings = json.load(f)


    # Iterate over each user data dictionary in users_data
    for user_data in users_data:
        user_info = user_data.get('Info', {})
        display_name = user_info.get('DisplayName')
        user_name = user_info.get('UserName')
        name = user_info.get('Name', {})
        family_name = name.get('FamilyName')
        given_name = name.get('GivenName')
        emails = user_info.get('Emails', [])
        email_data = None
        if emails:
            #Assuming only one email is present within user parameters
            email_data = emails[0]  

        if not (display_name and user_name and email_data and family_name and given_name):
            print(f"Skipping user due to missing required data: {user_data}")
            continue

        # Create the user using the Identity Store client
        try:
            emails_list = []
            if email_data:
                emails_list.append({
                    'Value': email_data.get('Value'),
                    'Type': email_data.get('Type'),
                    'Primary': email_data.get('Primary')
                })

            response = identitystore_client.create_user(
                IdentityStoreId=identity_store_id,
                UserName=user_name,
                DisplayName=display_name,
                Name={
                    'FamilyName': family_name,
                    'GivenName': given_name,
                },
                Emails=emails_list
            )
            new_user_id = response['UserId']
            print(f"Successfully created user: {user_name}")

            # Find the user's group names from the user-to-group mappings
            user_group_names = []
            for user_mapping in user_group_mappings:
                if user_mapping.get('UserName') == user_name:
                    user_group_names = [group_name for group_list in user_mapping.get('Groups', []) for group_name in group_list]
                    break

            # Add the user to the groups
            for group_name in user_group_names:
                for group_mapping in group_name_id_mappings:
                    if group_name in group_mapping:
                        group_id = group_mapping[group_name]
                        print(f"Adding user {user_name} to group {group_name} (ID: {group_id})")
                        response = identitystore_client.create_group_membership(
                            IdentityStoreId=identity_store_id,
                            GroupId=group_id,
                            MemberId={
                                'UserId':new_user_id
                            }
                        )
                        print(f"Response: {response}")
                        print(f"Added user {user_name} to group {group_name}")
                        break
                else:
                    print(f"Group {group_name} not found in the mappings")

        except identitystore_client.exceptions.ValidationException as e:
            print(f"ValidationException: {e}")
        except identitystore_client.exceptions.InternalServerException as e:
            print(f"InternalServerException: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


#EXAMPLE USAGE:
if __name__ == '__main__':
    file_path = '../mappings/groups_data.json'
    create_identity_center_groups(file_path)