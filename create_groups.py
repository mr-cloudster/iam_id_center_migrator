import json
import boto3

#CREATE GROUPS BASED ON MAPPED DATA
def create_identity_center_groups(file_path):
    # Create a session using your AWS credentials
    session = boto3.Session(profile_name='#DESTINATION_AWS_PROFILE#') #Replace with AWS CLI Profile name

    # IAM Identity Center instance details
    identity_store_id = '#DESTINATION_IDENTITY_STORE_ID#'  # Replace with target IAM Identity Center Identity Store ID

    # Create a client for the Identity Store
    identitystore_client = session.client('identitystore')
    
    # Read group data from JSON file
    with open(file_path, 'r') as f:
        groups_data = json.load(f)
    
    # Iterate over each group data and create groups in Identity Center
    new_groups_data = []
    DEFAULT_DESCRIPTION="Custom group"
    for group in groups_data:
        display_name = group['DisplayName']
        description = group['Description']
        if 'Description' in group:
            description = group['Description']
            if len(description) == 0:
                description = DEFAULT_DESCRIPTION
        # Create the group using the Identity Store client
        try:
            response = identitystore_client.create_group(
                IdentityStoreId=identity_store_id,
                DisplayName=display_name,
                Description=description,
            )
            new_group_id = response['GroupId']
            new_group_data = {display_name : new_group_id}
            new_groups_data.append(new_group_data)
            new_group_data_json = json.dumps(new_group_data, indent=2)
        
            print(f"Successfully created group: {display_name}")
        except identitystore_client.exceptions.ValidationException as e:
            print(f"ValidationException: {e}")
        except identitystore_client.exceptions.InternalServerException as e:
            print(f"InternalServerException: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


    try:
        with open('mappings/new_groups_data.json', 'r') as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    # Append the new data to the existing data
    existing_data.extend(new_groups_data)

    # Write the updated data to the file as a JSON array
    with open('mappings/new_groups_data.json', 'w') as f:
        json.dump(existing_data, f, indent=2)

# EXAMPLE USAGE:
if __name__ == '__main__':
    file_path = 'mappings/groups_data.json'
    create_identity_center_groups(file_path)