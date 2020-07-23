
from boto import ec2;
import csv;
import sys;
import pipes;
import os;
import subprocess;
import time;
import itertools
from sys import stderr;
from datetime import datetime

key_pair='Pils pair'
id_file="/home/jfc/.ssh/dss2_rsa"

region="us-west-2"
zone="us-west-2a"

class Options:
    user = None
    identity_file = None
    private_ips = False


def stop_instances(cluster, region=region, zone=zone):
    opts = Options();
    opts.user = "ec2-user"
    aaki = os.getenv('AWS_ACCESS_KEY_ID')
    asak = os.getenv('AWS_SECRET_ACCESS_KEY')
    if aaki is None:
        print("ERROR: The environment variable AWS_ACCESS_KEY_ID must be set")
        sys.exit(1)
    if asak is None:
        print("ERROR: The environment variable AWS_SECRET_ACCESS_KEY must be set")
        sys.exit(1)
    conn = ec2.connect_to_region(region, aws_access_key_id=aaki, aws_secret_access_key=asak);

    (mains, subordinates) = get_existing_cluster(conn, region, cluster);

    allnodes = mains + subordinates
    for node in allnodes:
        if node.state in ['running']:
            node.stop();



def get_existing_cluster(conn, region, cluster_name, die_on_error=True):
    """
    Get the EC2 instances in an existing cluster if available.
    Returns a tuple of lists of EC2 instance objects for the mains and subordinates.
    """
    print("Searching for existing cluster {c} in region {r}...".format(
          c=cluster_name, r=region))

    def get_instances(group_names):
        """
        Get all non-terminated instances that belong to any of the provided security groups.

        EC2 reservation filters and instance states are documented here:
            http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options
        """
        reservations = conn.get_all_reservations(
            filters={"instance.group-name": group_names})
        instances = itertools.chain.from_iterable(r.instances for r in reservations)
        return [i for i in instances if i.state not in ["shutting-down", "terminated"]]

    main_instances = get_instances([cluster_name + "-main"])
    subordinate_instances = get_instances([cluster_name + "-subordinates"])

    if any((main_instances, subordinate_instances)):
        print("Found {m} main{plural_m}, {s} subordinate{plural_s}.".format(
              m=len(main_instances),
              plural_m=('' if len(main_instances) == 1 else 's'),
              s=len(subordinate_instances),
              plural_s=('' if len(subordinate_instances) == 1 else 's')))

    if not main_instances and die_on_error:
        print("ERROR: Could not find a main for cluster {c} in region {r}.".format(
              c=cluster_name, r=region))
        sys.exit(1)

    return (main_instances, subordinate_instances)



stop_instances("bidcluster3")




