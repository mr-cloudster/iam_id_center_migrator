#FIRST WAVE DEPLOYMENT
read -p "Enter the source AWS profile: " SOURCE_AWS_PROFILE
sed -i '' "s/#SOURCE_AWS_PROFILE#/$SOURCE_AWS_PROFILE/g" ./data_mappings.py

#GET IAM CENTER VARIABLES AND UPDATES FILE
instances=$(aws sso-admin list-instances --profile "$SOURCE_AWS_PROFILE" --query 'Instances[*].IdentityStoreId' --output text)
instance_count=$(echo "$instances" | wc -l)
if [ "$instance_count" -gt 1 ]; then
    echo "Multiple instances found. Please enter the desired Identity Store ID:"
    echo "$instances"
    read -p "Identity Store ID: " SOURCE_IDENTITY_STORE_ID
else
    # Get the first item from the list
    SOURCE_IDENTITY_STORE_ID=$(echo "$instances" | head -n 1)
fi
sed -i '' "s/#SOURCE_IDENTITY_STORE_ID#/$SOURCE_IDENTITY_STORE_ID/g" ./data_mappings.py
echo "Source IAM Identity Center ID is: $SOURCE_IDENTITY_STORE_ID"

instance_arn=$(aws sso-admin list-instances --profile $SOURCE_AWS_PROFILE --query "Instances[?IdentityStoreId=='$SOURCE_IDENTITY_STORE_ID'].InstanceArn" --output text)
SOURCE_IDENTITY_STORE_ARN=$(echo "$instance_arn" | head -n 1)
echo "Source IAM Identity Center ARN is: $SOURCE_IDENTITY_STORE_ARN"
sed -i '' "s@#SOURCE_IDENTITY_STORE_ARN#@$SOURCE_IDENTITY_STORE_ARN@g" ./data_mappings.py
sleep 3
echo "Variables loaded into data_mapping.py file successfuly..."
sleep 3

#START DATA MAPPINGS
echo "IAM Identity Center Mapping will now start...."
sleep 3
python3 data_mappings.py
echo "First wave completed!"