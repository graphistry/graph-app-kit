#!/bin/bash
set -e

#
# List Graphistry AMIs for yml
#
# Run: $ VERSION=2.36.6-11.0 ./graphistry-ami-list.sh
#
# Output: Non-zero return code on failure, and on success:
#
#eu-north-1:
#  "HVM64": "ami-007f7e0cbb31804ca"
#ap-south-1:
#  "HVM64": "ami-0771ea144a8bcc05b"
#eu-west-3:
#  "HVM64": "ami-0bf29fec2ad97b43b"
# ...
#
# ------------

AWS=*
BASE=graphistry-standalone-2???-??-??T??-??-??Z-v
VERSION=${VERSION:-2.35.9-11.0}
SUFFIX=*
GREP_INCLUDE="aws-marketplace/graphistry-standalone"  # There were some surprise namespaces 

## {"ImageId": ..., "ImageLocation": ..., "region": ...}*
IMAGES=$( 
    for region in `aws ec2 describe-regions --output text | cut -f4`
    do
        aws ec2 describe-images \
            --region $region \
            --owners self 679593333241 \
            --filters "Name=name,Values=${AWS}${BASE}${VERSION}${SUFFIX}" \
        | jq -c "(.Images[] | {ImageId: .ImageId, ImageLocation: .ImageLocation, "region": \"$region\"})" \
        | grep "${GREP_INCLUDE}"
    done
)

#echo "IMAGES: $IMAGES"
#echo "IMAGES: $( echo "$IMAGES" | jq -r . )"

#From ^^^, we want:
#Mappings: 
#  RegionMap: 
#    us-east-1: 
#      "HVM64": "ami-0758d945357560324"
for row in `echo "$IMAGES"`; do
    REGION=$(echo $row | jq -r .region)
    IMAGE=$(echo $row | jq -r .ImageId)
    LOC=$(echo $row | jq -r .ImageLocation)
    echo "${REGION}:"
    echo "  \"HVM64\": \"$IMAGE\""
    #echo "  ($LOC)"
done
