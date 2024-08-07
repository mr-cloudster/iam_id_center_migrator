#FIRST WAVE DEPLOYMENT
read -p "Enter the source AWS profile: " DESTINATION_AWS_PROFILE
sed -i '' "s/#DESTINATION_AWS_PROFILE#/$DESTINATION_AWS_PROFILE/g" ./functions/create_users.py
sed -i '' "s/#DESTINATION_AWS_PROFILE#/$DESTINATION_AWS_PROFILE/g" ./functions/create_groups.py
sed -i '' "s/#DESTINATION_AWS_PROFILE#/$DESTINATION_AWS_PROFILE/g" ./functions/create_permission_sets.py

#GET IAM CENTER VARIABLES AND UPDATES FILE
instances=$(aws sso-admin list-instances --profile "$DESTINATION_AWS_PROFILE" --query 'Instances[*].IdentityStoreId' --output text)
instance_count=$(echo "$instances" | wc -l)
if [ "$instance_count" -gt 1 ]; then
    echo "Multiple instances found. Please enter the desired Identity Store ID:"
    echo "$instances"
    read -p "Identity Store ID: " DESTINATION_IDENTITY_STORE_ID
else
    # Get the first item from the list
    DESTINATION_IDENTITY_STORE_ID=$(echo "$instances" | head -n 1)
fi

sed -i '' "s/# v#/$DESTINATION_IDENTITY_STORE_ID/g" ./functions/create_users.py
sed -i '' "s/#DESTINATION_IDENTITY_STORE_ID#/$DESTINATION_IDENTITY_STORE_ID/g" ./functions/create_groups.py
sed -i '' "s/#DESTINATION_IDENTITY_STORE_ID#/$DESTINATION_IDENTITY_STORE_ID/g" ./functions/create_permission_sets.py

echo "Destination IAM Identity Center ID is: $DESTINATION_IDENTITY_STORE_ID"
echo "Variables successfuly loaded..."

#START MIGRATION
echo "IAM Identity Center migration will now start...."
echo "Creating Groups..."
sleep 3
python3 functions/create_groups.py
echo "Creating Permission Sets and mapping them to their respective AWS Accounts..."
sleep 3
python3 functions/create_permission_sets.py
sleep 3
echo "Users will now be created and added to their respective groups..."
python3 functions/create_users.py
echo "Second wave completed!"