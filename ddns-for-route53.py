import boto3, time, requests, sys, os
from botocore.exceptions import ClientError

def checkHostAddr(client, hostzoneId, domainName):
    addr = ''
    
    try:
        res = client.list_resource_record_sets(
                HostedZoneId=hostzoneId,
                StartRecordType='A',
                StartRecordName=domainName,
                MaxItems='1'
        )
    except ClientError as e:
        print(e.response['Error']['Code'])
        return addr

    for record in res['ResourceRecordSets']:
        if record['Type'] == 'A':
            for r in record['ResourceRecords']:
                addr = r['Value']
                ipFlag = True
        if ipFlag == True:
            break
    
    return addr
    


def updateIpAdder(client, hostzoneId, domainName, ipAddr):
    try:
        response = client.change_resource_record_sets(
            HostedZoneId = hostzoneId,
            ChangeBatch={
                'Comment': 'Updating A record for dynamic IP',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': domainName, 
                            'Type': 'A',
                            'TTL': 60,
                            'ResourceRecords': [
                                {'Value': ipAddr}
                            ]
                        }
                    }
                ]
            }
        )
    except ClientError as e:
        print(e.response['Error']['Code'])
        return -1

    return response


def main():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    print(current_directory)
    try:
        config = open(f'{current_directory}/config', 'r')

        AWS_ACCESS_KEY_ID = config.readline().split(' ')[1].replace('\n', '')
        AWS_SECRET_ACCESS_KEY = config.readline().split(' ')[1].replace('\n', '')
        AWS_HOSTZONE_ID = config.readline().split(' ')[1].replace('\n', '')
        DOMAIN_NAME = config.readline().split(' ')[1].replace('\n', '')
        
        config.close()
    except Exception as e:
        print('config file is missing')

    if AWS_ACCESS_KEY_ID == 'YOUR_ACCESS_KEY_ID' or AWS_SECRET_ACCESS_KEY == 'YOUR_ACCESS_KEY' or AWS_HOSTZONE_ID == 'YOUR_HOSTZONE_ID' or DOMAIN_NAME == 'YOUR_DOMAIN':
        print('please update config file!')
        sys.exit()

    client = boto3.client(
        'route53',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_HOSTZONE_ID
    )

    currentIp = requests.get('http://checkip.amazonaws.com/get').text.replace('\n', '')
    print(f'Current IP Address: {currentIp}')
    
    cnt = 0
    ipAddr = ''
    while cnt <= 5:
        ipAddr = checkHostAddr(client, AWS_HOSTZONE_ID, DOMAIN_NAME)
        if ipAddr != '':
            print(f'Hosted IP Address: {ipAddr}')
            break
        else:
            sys.exit()

    if ipAddr != '':
        if ipAddr != currentIp:
            print('Updating IP Address')
            for i in range(0, 2):
                res = updateIpAdder(client, AWS_HOSTZONE_ID, DOMAIN_NAME, currentIp)
                if res != -1:
                    ipAddr = checkHostAddr(client, AWS_HOSTZONE_ID, DOMAIN_NAME)
                    if ipAddr == currentIp:
                        print(f'{ipAddr} : {currentIp}')
                        print('The IP address has been successfully updated.')
                        sys.exit()
                    else:
                        print(f'IP address update failed. Retrying({i+1}).')         
        if ipAddr == currentIp:
            print('The hosted IP matches the current IP address.')
            sys.exit()
    
    print('IP address update failed.')
    sys.exit()
    

if __name__ == '__main__':
    main()