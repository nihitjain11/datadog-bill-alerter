# About
* terraform.tfvars - values for required variables
* main.tf, variables.tf - terraform code
* main.py - billing script for fetching bill and sending alerts on slack and email
* requirements.txt - package requirements for main.py script
* archive.zip - zip file archiving main.py & requirements.txt

# Steps to run
1. update `terraform.tfvars` to update Budget, Slack_Webhook, Email for alerts
2. create function zip: `zip archive.zip main.py requirements.txt`
3. run terraform: init, validate, plan, apply
