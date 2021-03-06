import sys, getpass, json, time, argparse, requests
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *

# import file with virt/pool info
from virt_info import *

def create_pool(bigip, name, members, lb_method, bigip_url, monitor_method):
        payload = {}

        # convert member format
        members = [ { 'kind' : 'ltm:pool:members', 'name' : member } for member in POOL_MEMBERS ]

        # define payload values for pool
        payload['kind'] = 'tm:ltm:pool:poolstate'
        payload['name'] = name
        payload['description'] = name
        payload['loadBalancingMode'] = lb_method
        payload['monitor'] = monitor_method
        payload['members'] = members

        pool_result = bigip.post('%s/ltm/pool' % bigip_url, data=json.dumps(payload))
        print pool_result.text

def create_http_virtual(bigip, name, address, port, pool, bigip_url):
        payload = {}

        #define payload values for vs
        payload['kind'] = 'tm:ltm:virtual:virtualstate'
        payload['name'] = name
        payload['description'] = name
        payload['destination'] = '%s:%s' % (address, port)
        payload['mask'] = '255.255.255.255'
        payload['ipProtocol'] = 'tcp'
        payload['sourceAddressTranslation'] = { 'type' : 'snat' }
        payload['profiles'] = [
                { 'kind' : 'ltm:virtual:profile', 'name' : 'http' },
                { 'kind' : 'ltm:virtual:profile', 'name' : 'tcp' }
        ]
        payload['snatpool'] = 'inside'
        payload['pool'] = pool

        vs_result = bigip.post('%s/ltm/virtual' % bigip_url, data=json.dumps(payload))
        print vs_result.text



# Inserts route to VS into that site's aggregation switch
def insertRoute(host, user, password, vs, nexthop):

        dev = Device(host=host, user=user, password=password)

        try:
                dev.open()
        except Exception as err:
                print "Cannot connect to device", err
        dev.bind ( cu=Config )
        dev.cu.load("set routing-options static route {0} next-hop {1}".format(vs, nexthop))
        try:
                dev.cu.commit()
        except CommitError as err1:
                print "device: {0}".format(host), err1
                print "Rolling back configuration"
                dev.cu.rollback(rb_id=1)
                dev.cu.commit
                dev.close()
                sys.exit(2)
        dev.close()
        sys.exit(3)


def main():
        parser = argparse.ArgumentParser(description="Creates a Virtual Server and corresponding pool on an F5, inserts route for VS")
        parser.add_argument("-c", dest="COLO", required=True, choices=["den", "phx"], type=str, help="The DC in which the virt will reside, 'den' or 'phx'")
        parser.add_argument("-u", dest="USERID", required=True, help="Your username")
        args = parser.parse_args()

# Assign a few things based on which colo is specified
        PARAMS = {
        "den" : {
                "AGSW": "den2agsw01",
                "LTM": "den2adc01",
                "NEXT_HOP": "10.2.255.10"
                },
        "phx" : {
                "AGSW": "phx1agsw01",
                "LTM": "phx1adc01",
                "NEXT_HOP": "10.4.255.10"
                }
        }
AGSW = PARAMS[args.COLO]['AGSW']
        LTM = PARAMS[args.COLO]['LTM']
        NEXT_HOP = PARAMS[args.COLO]['NEXT_HOP']

# Requests requires a full URL to be sent as arg for every request, define base URL globally here
        BIGIP_URL_BASE = 'https://%s/mgmt/tm' % LTM

        SLEEP_TIME = 20

# Get password
        HIDEPASS = getpass.getpass()

# REST resource for BIG-IP that all other requests will use
        bigip = requests.session()
        bigip.auth = (args.USERID, HIDEPASS)
        bigip.verify = False
        bigip.headers.update({'Content-Type' : 'application/json'})
        print "created REST resource for BIG-IP at %s..." % LTM

# create pool
        create_pool(bigip, POOL_NAME, POOL_MEMBERS, POOL_LB_METHOD, BIGIP_URL_BASE, POOL_MONITOR)
        print "created pool \"%s\" with members %s..." % (POOL_NAME, ", ".join(POOL_MEMBERS))

# create virtual
        create_http_virtual(bigip, VS_NAME, VS_ADDRESS, VS_PORT, POOL_NAME, BIGIP_URL_BASE)
        print "created virtual server \"%s\" with destination %s:%s..." % (VS_NAME, VS_ADDRESS, VS_PORT)

# sleep for a little while
        print "sleeping for %s seconds, check for successful creation..." % SLEEP_TIME
        time.sleep(SLEEP_TIME)

        insertRoute(AGSW, args.USERID, HIDEPASS, VS_ADDRESS, NEXT_HOP)

if __name__ == "__main__":
        main()
