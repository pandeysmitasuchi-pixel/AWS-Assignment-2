# AWS-Assignment-2
---

## Assignment 2: Automated EBS Snapshot Creation and Cleanup

### Implementation Steps
1. Identified target EBS Volume (`vol-xxxxxxxxxxxxxxxxx`).
2. Configured an IAM Role with permissions for `ec2:CreateSnapshot`, `ec2:DescribeSnapshots`, `ec2:DeleteSnapshot`, and `ec2:CreateTags`.
3. Created Python 3.12 Lambda code using `boto3` to snapshot the volume, tag it with `CreatedBy=Lambda-Backup`, and evaluate cutoff timestamps using timezone-aware UTC dates.
4. Scheduled automatic execution using Amazon EventBridge Scheduler with a weekly cron pattern (`cron(0 0 ? * SUN *)`).

### Screenshots & Proof of Work

#### 1. IAM Role & Inline Policy
![IAM Policy](screenshots/assignment2_iam_role.png)

#### 2. Lambda Configuration
![Lambda Setup](screenshots/assignment2_lambda_config.png)

#### 3. Test Invocation & Output
![Test Invocation](screenshots/assignment2_test_invocation.png)

#### 4. CloudWatch Logs
![CloudWatch Logs](screenshots/assignment2_cloudwatch_logs.png)

#### 5. EC2 Console Snapshot Output
![EC2 Snapshots](screenshots/assignment2_final_result.png)

---

### Discussion Point: Lambda vs. AWS Data Lifecycle Manager (DLM)
AWS Data Lifecycle Manager (DLM) provides native, automated backup management for EBS volumes without writing code. However, AWS Lambda remains the superior choice when:
1. **Custom Conditional Logic:** Backup execution requires dynamic filtering, custom pre-checks, or multi-tag evaluation rules beyond DLM's standard scheduling options.
2. **Cross-Account & Cross-Region Transfers:** Snapshots must be automatically copied to secondary accounts or regions with custom KMS keys applied dynamically.
3. **Custom Event Notifications:** Backup successes or failures must trigger custom payloads directly to webhooks (e.g., Slack, MS Teams, Datadog) rather than raw SNS messages.
