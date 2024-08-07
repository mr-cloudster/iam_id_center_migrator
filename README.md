# IAM Identity Center Migrator

This project is intended to migrate resources from an IAM Identity Center and recreate them within another AWS Organization.

# How to use it?

This project should be run in two waves.

## First wave:

### Collects users, groups, permission sets and its mappings within the source account.

**Considerations:**
> **-** Run this on an earlier phase of Control Tower delivery.
> **-** Check files within "src/mappings/examples/" to understand what is collected.
> **-** Keep in mind that this is a first version, improvements are most welcome.

**Steps:**
> **1.** Generate AWS IAM Keypair with the necessary permission from the source account.
> **2.** Create an AWS CLI profile using the generated credentials.
> **3.** Install python dependencies and run "firs_wave.sh".

---

## Second wave:

### Loads everything into the destination account.

**Considerations:**

> **-** Run this at the latest phase of Control Tower delivery.
> **-** Check that desired AWS accounts are enrolled into the new Organization.
> **-** Keep in mind that users created can receive emails.

**Steps:**

> **1.** Log into AWS Identity Center console on the destination AWS Account and enable sending emails via the API.
>> **IAM ID Center > Settings > Authentication > Standard Authentication > Configure > Send email OTP > Save**
> **2.** Generate AWS IAM Keypair with the necessary permission from the destination account.
> **3.** Create an AWS CLI profile using the generated credentials.
> **4.** Verify the collected data on the first wave to be sure is correct.
> **5.** Run "second_wave.sh"

---

# Improvements

1. Permission Sets can contain Custom or Inline IAM Policies. Automate this policy creation and migration. 
2. User data is limited to Primary Information only, if more details are needed, add them. (Example: Contact methods, Address, etc).
3. Any setting is replicated, example; access portal URL should be manually added into the destination account.