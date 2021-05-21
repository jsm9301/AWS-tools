#!/bin/bash

### AWS CLI Sample with bash shell

create_VPC(){
  VPC_ID=$(aws ec2 create-vpc \
  --cidr-block $VPC_CIDR \
  --query 'Vpc.{VpcId:VpcId}' \
  --output text \
  --region $AWS_REGION)

  # Add Name tag to VPC
  aws ec2 create-tags \
  --resources $VPC_ID \
  --tags "Key=Name,Value=$VPC_NAME" \
  --region $AWS_REGION

  echo $VPC_ID
}

set_pub_sub(){
  SUBNET_PUBLIC_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block $1 \
    --availability-zone $2 \
    --query 'Subnet.{SubnetId:SubnetId}' \
    --output text \
    --region $AWS_REGION)

  # Add Name tag to Public Subnet
  aws ec2 create-tags \
    --resources $SUBNET_PUBLIC_ID \
    --tags "Key=Name,Value=$3" \
    --region $AWS_REGION
}

set_pri_sub(){
  SUBNET_PRIVATE_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block $1 \
    --availability-zone $2 \
    --query 'Subnet.{SubnetId:SubnetId}' \
    --output text \
    --region $AWS_REGION)

  # Add Name tag to Private Subnet
  aws ec2 create-tags \
    --resources $SUBNET_PRIVATE_ID \
    --tags "Key=Name,Value=$3" \
    --region $AWS_REGION
}

get_az(){
  tmp=`expr $1 % 2`
  AZ=""
  if [ $tmp -eq 1 ]; then
    AZ="a"
  else
    AZ="c"
  fi

  echo $AZ
}

make_subnet_CIDR(){
  start=$1
  end=$2
  sub_list=()

  sub_CIDR=$(echo $VPC_CIDR | tr "." "\n")
  CIDR_array=()
  for CIDR in $sub_CIDR
  do
    CIDR_array+=($CIDR)
  done

  for ((i=$start;i<$end;i++));
  do
    sub_list+=("${CIDR_array[0]}.${CIDR_array[1]}.$i.0/24")
  done

  echo ${sub_list[@]}
}

create_pub_sub(){
  pub_sub_num=$1

  # Add Public Subnet CIDR start with 0
  _CIDR=$(make_subnet_CIDR 1 `expr $pub_sub_num + 1`)
  CIDR_list=()
  for CIDR in $_CIDR
  do
    CIDR_list+=($CIDR)
  done

  # Create Public Subnet with pub_sub_list
  for ((i=0;i<pub_sub_num;i++));
  do
    num=`expr $i + 1`
    AZ=$(get_az $num)
    name="PubSub-$num-$AZ"
    set_pub_sub ${CIDR_list[$i]} $AWS_REGION$AZ $name

    echo "------Created $name-------"
  done
}

create_pri_sub(){
  pri_sub_start=$1
  pri_sub_end=$2

  _CIDR=$(make_subnet_CIDR $pri_sub_start $pri_sub_end)
  CIDR_list=()
  for CIDR in $_CIDR
  do
    CIDR_list+=($CIDR)
  done

  # Create Private Subnet with pri_sub_list
  for ((i=0;i<$pri_sub_num;i++));
  do
    num=`expr $i + 1`
    AZ=$(get_az $num)
    name="PriSub-$num-$AZ"
    set_pri_sub ${CIDR_list[$i]} $AWS_REGION$AZ $name

    echo "------Created $name-------"
  done
}

#---------- input ----------
echo -e "enter the region: "
read AWS_REGION

echo -e "enter the VPC name: "
read VPC_NAME

echo -e "enter the VPC CIDR: "
read VPC_CIDR


#---------- Default Parameters ----------
if [ x$AWS_REGION == x ]; then
  AWS_REGION="us-east-2"
fi
#AWS_REGION="us-east-2"
#VPC_NAME="TEST-VPC"
#VPC_CIDR="10.0.0.0/16"
pub_sub_num=2
pri_sub_num=2
pri_start=`expr $pub_sub_num + $pri_sub_num - 1`
pri_end=`expr $pri_start + $pri_sub_num`
#--------------------------------

#---------- create VPC & Subnet ----------
VPC_ID=$(create_VPC)

create_pub_sub $pub_sub_num
create_pri_sub $pri_start $pri_end