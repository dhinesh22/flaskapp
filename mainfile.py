from flask import Flask, render_template, request
import boto3
import csv
from time import sleep
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/flaskapplication', methods=['POST'])
def success():
    securitygroups = []
    if request.method == 'POST':
        instancecount = request.form['instancecount']
        imageid = request.form['imageid']
        instancetype = request.form['instancetype']
        keyname = request.form['keyname']
        securitygroup = request.form['securitygroup']
        spotprice = request.form['spotprice']
        tvalue = request.form['tvalue']

        instancecount = int(instancecount)
        securitygroups.append(securitygroup)

        client = boto3.client('ec2', region_name='us-east-1')
        req = client.request_spot_instances(InstanceCount=instancecount,
                                            Type='one-time',
                                            InstanceInterruptionBehavior='terminate',
                                            LaunchSpecification={
                                                'SecurityGroups': securitygroups,
                                                'ImageId': imageid,
                                                'InstanceType': instancetype,
                                                'KeyName': keyname,
                                            },
                                            SpotPrice=spotprice
                                            )
        print('Spot request created, status: ' + req['SpotInstanceRequests'][0]['State'])
        print('Waiting for spot provisioning')
        sleep(10)
        print(req)
        while True:
            spotrequestid = req['SpotInstanceRequests'][0]['SpotInstanceRequestId']
            current_req = client.describe_spot_instance_requests(
                SpotInstanceRequestIds=[req['SpotInstanceRequests'][0]['SpotInstanceRequestId']])
            instanceid = current_req['SpotInstanceRequests'][0]['InstanceId']
            if current_req['SpotInstanceRequests'][0]['State'] == 'active':
                sleep(1)
                print('SpotInstanceRequests allocated ,Id: ',
                      current_req['SpotInstanceRequests'][0]['SpotInstanceRequestId']
                      )
                client.create_tags(Resources=[current_req['SpotInstanceRequests'][0]['SpotInstanceRequestId']],
                                   Tags=[{
                                       'Key': 'Name',
                                       'Value': tvalue
                                   }]
                                   )
                print('Waiting...', sleep(1))
                print(current_req)
                bitprice = current_req['SpotInstanceRequests'][0]['SpotPrice']
                time = current_req['ResponseMetadata']
                time1 = time['HTTPHeaders']
                ltime = time1['date']
                # value = current_req['SpotInstanceRequests'][0]['Tags'][0]
                # tvalues = value['Value']
                value = client.describe_tags(
                    Filters=[
                        {
                            'Name': 'resource-id',
                            'Values': [spotrequestid],
                        },
                    ],
                )
                value1 = value['Tags'][0]
                tvalues = value1['Value']
                req = client.describe_instances(InstanceIds=[instanceid])
                publicdns = req['Reservations'][0]['Instances'][0]['PublicDnsName']
                print(current_req)
                print(spotrequestid)
                print(instanceid)
                print(bitprice)
                print(ltime)
                print(tvalues)
                print(publicdns)
                myfile = open('awsfile.csv', 'a')
                with myfile:
                    myfields = ['Instance Name', 'Public DNS', 'Date&Time', 'Spot price',
                                'Instance Id']
                    writer = csv.DictWriter(myfile, fieldnames=myfields)
                    writer.writerow({'Instance Name': tvalues, 'Public DNS': publicdns, 'Date&Time': ltime,
                                     'Spot price': bitprice, 'Instance Id': instanceid}
                                    )
                if current_req['SpotInstanceRequests'][0]['State'] == 'active':
                    return render_template('success.html')

    else:
        pass


@app.route('/instancedetails', methods=['POST'])
def instdetails():
    if request.method == 'POST':
        myfilepath = '/home/plexoware/PycharmProjects/flaskapplication/awsfile.csv'
        with open(myfilepath, "r") as f:
            reader = csv.reader(f, delimiter=",")
            data = list(reader)
            n = len(data)
        for i in range(1, n):
            with open(myfilepath, 'rt') as f:
                mycsv = csv.reader(f)
                mycsv = list(mycsv)
                return render_template('instance_details.html', values=mycsv)

        '''client = boto3.client('ec2')
        #tvalues = []
        tvalue = request.form['tvalue']
        bitprice = request.form['bitprice']
        #client = boto3.client('ec2')
        #tvalues.append(tvalue)
        #current_req = client.describe_tags()
        #tvalue = current_req['Tags'][0]['Key']
        #tvalue = tvalues
        req1 = client.describe_instances()
        n = len(req1['Reservations'])
        for i in (0, n):
            req1 = client.describe_spot_instance_requests()
            #val = req1['Reservations'][i]['Instances'][0]['State'][0]
            if req1['SpotInstanceRequests'][i]['State'] == 'active':
                print('running')
                req = client.describe_instances(InstanceIds=['string'])
                ltime = req['Reservations'][i]['Instances'][0]['LaunchTime']
                publicdns = req['Reservations'][i]['Instances'][0]['PublicDnsName']
                #req2 = client.describe_spot_instance_requests()
                #bitprice = req2['SpotInstanceRequests'][0]['SpotPrice']'''


@app.route('/terminated', methods=['POST'])
def stopping():
    if request.method == 'POST':
        instanceid = request.form['instanceid']
        print(instanceid)
        if request.form['submit'] == 'TERMINATE':
            client = boto3.client('ec2')
            # current_req = client.describe_spot_instance_requests(
            #     Filters=[
            #         {
            #             'Name': 'instance-id',
            #             'Values': [
            #                 instanceid,
            #             ]
            #         },
            #     ],
            # )
            # if current_req['SpotInstanceRequests'][0]['State'] == 'active':
            term = client.terminate_instances(
                InstanceIds=[
                    instanceid,
                ],
                DryRun=False
            )
            return render_template('terminated.html')
        elif request.form['submit'] == 'STOP':
            client = boto3.client('ec2')
            sto = client.stop_instances(
                InstanceIds=[
                    instanceid,
                ]
            )
            return render_template('terminated.html')
        # elif current_req['SpotInstanceRequests'][0]['State'] == 'closed':
        #     return render_template('terminated.html')
        else:
            pass


if __name__ == "__main__":
    app.run(debug=True)

# client.delete_tags(Resources=[ami-06e441c14766d8bb7],Tags=[{"Key": my-t3-nano-instance}])
# aws ec2 delete-tags --resources i-0f1f9ff06ba6e6047 --tags Key=Name,Value=a4-t3-nano-instance
# aws ec2 cancel-spot-instance-requests --spot-instance-request-ids sir-zxer7dxh
# aws ec2 terminate-instances --instance-ids i-0befd484fcad66f70 i-0028585c98141ab38 i-06f9c5565fe94278f
