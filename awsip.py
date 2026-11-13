import urllib.request
import json
import ipaddress
import sys

def download_aws_ip_set():
  """Downloads the AWS IP range JSON file and returns it as a dictionary."""
  # URL of the AWS IP range JSON file
  aws_ip_range_url = 'https://ip-ranges.amazonaws.com/ip-ranges.json'
  # Download the JSON file
  with urllib.request.urlopen(aws_ip_range_url) as url:
    aws_ip_range_data = json.load(url)
  return aws_ip_range_data['prefixes']


def find_aws_ip(aws_ip_range_data, ip_to_find):

  """Finds the AWS IP range that contains the given IP address."""
  results = []
  target_ip = ipaddress.ip_address(ip_to_find)
  for prefix in aws_ip_range_data:
    network = ipaddress.ip_network(prefix['ip_prefix'])
    if target_ip in network:
      entry = dict(prefix)
      entry['first_ip'] = str(network.network_address)
      entry['last_ip'] = str(network.broadcast_address)
      entry['ip_count'] = network.num_addresses
      results.append(entry)
  return results

def find_smallest_subnet(ip_strings):
  """Finds the smallest subnet that contains all the given IP addresses."""
  if not ip_strings:
    raise ValueError("At least one IP adress must be provided.")
  ips = [ipaddress.ip_address(ip) for ip in ip_strings]
  min_ip, max_ip = min(ips), max(ips)
  subnet = ipaddress.ip_network(min_ip)
  while max_ip not in subnet:
    subnet = subnet.supernet()
  return subnet

def find_aws_subnet(aws_ip_range_data, ip_strings):
    """Finds the smallest subnet for the given IPs and checks if it belongs to AWS."""
    target_subnet = find_smallest_subnet(ip_strings)
    matching_ranges = []

    for prefix in aws_ip_range_data:
        aws_network = ipaddress.ip_network(prefix['ip_prefix'])
        if aws_network.version == target_subnet.version and target_subnet.subnet_of(aws_network):
            entry = dict(prefix)
            entry['first_ip'] = str(aws_network.network_address)
            entry['last_ip'] = str(aws_network.broadcast_address)
            entry['ip_count'] = aws_network.num_addresses
            matching_ranges.append(entry)

    return {
        'input_ips': ip_strings,
        'smallest_subnet': str(target_subnet),
        'subnet_ip_count': target_subnet.num_addresses,
        'aws_matches': matching_ranges
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python awsip.py <ip1> [ip2 ... ipN]\n")
        sys.exit(1)
    result = find_aws_subnet(download_aws_ip_set(), sys.argv[1:])
    sys.stdout.write(json.dumps(result, indent=2) + "\n")