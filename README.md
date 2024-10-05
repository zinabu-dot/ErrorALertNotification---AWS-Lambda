# ErrorALertNotification - AWS-Lambda
When there is an error in your lambda function, this lambda function helps you to be notified/alarmed about the failed lambda function, triggered  by the cloudwatch log key words like ?ERROR ?Error, etc.

Steps:

1. Create sns TOPIC in AWS SNS TOPICs service
2. Create an environmental variable with the ARN value of the created topic (as value)
3. Trigger on CLOUDWATCH LOG groups (the functions from which you want to receive an alarm)
4. Test it (just run your lambda function (the function you wanted to get the alarm for) with an event).
   
