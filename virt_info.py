# info for vs/pool

VS_NAME = 'VS_test'
VS_ADDRESS = '10.2.253.100'
VS_PORT = '80'
POOL_NAME = 'Pool_test'

# pool monitor type
POOL_MONITOR = 'gateway_icmp'

# pool load balancing method
POOL_LB_METHOD = 'least-connections-member'

# list of pool members, should be in ip:port format, must match the VS_PORT value.
POOL_MEMBERS = [ 'den2net01:80' ]
