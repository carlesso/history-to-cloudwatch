ARG BUILD_FROM
FROM $BUILD_FROM

# The core of the addon is a python script, so we install python
# and the dependencies we need.
RUN apk add --no-cache python3 py3-pip
RUN pip3 install --no-cache-dir boto3 requests

COPY history-to-cloudwatch.py /
RUN chmod +x /history-to-cloudwatch.py
CMD [ "/history-to-cloudwatch.py" ]