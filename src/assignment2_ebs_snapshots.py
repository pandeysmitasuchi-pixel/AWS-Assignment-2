import boto3
from datetime import datetime, timezone, timedelta

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Target EBS Volume ID (Replace with your actual EC2 Volume ID)
VOLUME_ID = "vol-0123456789abcdef0"  

# Set TEST_MODE = True to delete snapshots older than 0 minutes (instant testing)
# Set TEST_MODE = False for production logic (snapshots older than 30 days)
TEST_MODE = True

RETENTION_DAYS = 30
BACKUP_TAG_KEY = "CreatedBy"
BACKUP_TAG_VALUE = "Lambda-Backup"
# ==============================================================================

ec2_client = boto3.client('ec2')

def lambda_handler(event, context):
    """
    Creates a new snapshot of the designated EBS volume, tags it, 
    and purges older snapshots matching the retention criteria.
    """
    print(f"INFO: Starting EBS Snapshot automation for Volume ID: {VOLUME_ID}")
    
    # --------------------------------------------------------------------------
    # STEP 1: Create and Tag New EBS Snapshot
    # --------------------------------------------------------------------------
    description = f"Automated backup of {VOLUME_ID} created by Lambda"
    
    try:
        create_response = ec2_client.create_snapshot(
            VolumeId=VOLUME_ID,
            Description=description,
            TagSpecifications=[
                {
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {'Key': BACKUP_TAG_KEY, 'Value': BACKUP_TAG_VALUE},
                        {'Key': 'Name', 'Value': f"Backup-{VOLUME_ID}"}
                    ]
                }
            ]
        )
        new_snapshot_id = create_response['SnapshotId']
        print(f"CREATED: Snapshot ID='{new_snapshot_id}' for Volume='{VOLUME_ID}'")
    except Exception as e:
        print(f"ERROR: Failed to create snapshot for volume {VOLUME_ID}: {str(e)}")
        raise e

    # --------------------------------------------------------------------------
    # STEP 2: Evaluate Cutoff Time & Describe Existing Snapshots
    # --------------------------------------------------------------------------
    if TEST_MODE:
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=0)
        print("INFO: Operating in TEST MODE (Retention: > 0 minutes)")
    else:
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
        print(f"INFO: Operating in PRODUCTION MODE (Retention: > {RETENTION_DAYS} days)")

    print(f"INFO: Snapshot Cutoff Date (UTC): {cutoff_time.isoformat()}")

    # Fetch snapshots owned by 'self' that match our custom tag
    describe_response = ec2_client.describe_snapshots(
        OwnerIds=['self'],
        Filters=[
            {'Name': f'tag:{BACKUP_TAG_KEY}', 'Values': [BACKUP_TAG_VALUE]},
            {'Name': 'volume-id', 'Values': [VOLUME_ID]}
        ]
    )

    deleted_snapshots = []
    total_evaluated = len(describe_response['Snapshots'])

    # --------------------------------------------------------------------------
    # STEP 3: Purge Expired Snapshots
    # --------------------------------------------------------------------------
    for snapshot in describe_response['Snapshots']:
        snap_id = snapshot['SnapshotId']
        start_time = snapshot['StartTime']  # Returned in UTC timezone-aware format

        # Prevent deleting the snapshot we just created in this execution run
        if snap_id == new_snapshot_id:
            continue

        if start_time < cutoff_time:
            try:
                ec2_client.delete_snapshot(SnapshotId=snap_id)
                deleted_snapshots.append(snap_id)
                print(f"DELETED: Snapshot ID='{snap_id}' | StartTime='{start_time.isoformat()}'")
            except Exception as e:
                print(f"ERROR: Failed to delete snapshot {snap_id}: {str(e)}")

    # --------------------------------------------------------------------------
    # STEP 4: Execution Summary Output
    # --------------------------------------------------------------------------
    print(f"SUMMARY: Evaluated {total_evaluated} total snapshots. Created: 1 | Deleted: {len(deleted_snapshots)}")

    return {
        'statusCode': 200,
        'volume_id': VOLUME_ID,
        'created_snapshot_id': new_snapshot_id,
        'deleted_snapshot_ids': deleted_snapshots,
        'total_evaluated': total_evaluated
    }
