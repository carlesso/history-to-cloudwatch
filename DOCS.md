# History to Cloudwatch 
This addon will send the data of you sensors to [AWS CloudWatch](https://aws.amazon.com/cloudwatch/) as metrics.


## Configuration
* `sensors`: list of sensors to monitor, comma separated. Currently tested with temperature and humidity sensors.
* `cloudwatch-namespace`: the cloudwatch namespace for your metrics, defaults to `Home Assistant`.
* `aws-access-key`: AWS access key for your account.
* `aws-secret-key`: AWS secret key for your account.
* `aws-region`: which AWS region to send your metrics, defaults to `us-west-2`.