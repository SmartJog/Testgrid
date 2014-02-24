#!/bin/bash                                                                                                                                                                                                                 
#chmod a+x test.sh
set -e -o pipefail


#read -p "Enter the IP of your router:          (looks like 192.168.1.1)   " routerip
#echo "$routerip"
#
#/etc/init.d/networking restart
#check if partition exist


PACKAGE_IS="kvm libvirt-bin virtinst gdisk kpartx  mdadm  python-progressbar=2.3-0.2 python-installsystems installsystems"
PACKAGE="lvm2 bridge-utils"
VOLUME_XML_TEMPLATE="vg_template.xml"
BRIDGE_TEMPLATE="template_bridge.txt"
PV_NAME="/dev/sda6"
VG_NAME="vg"
BRIDGE_NAME="br2006"
DEVICE="eth1"


if brctl show | grep $BRIDGE_NAME
then 
    echo "$(tput setaf 1)bridge ${BRIDGE_NAME} exist$(tput sgr0)"
else
    sed -e "s/\${bridge_name}/${BRIDGE_NAME}/" -e "s/\${device}/${DEVICE}/" $BRIDGE_TEMPLATE >> "/etc/network/interfaces"
    ifup $BRIDGE_NAME
fi



for pkg in $PACKAGE $PACKAGE_IS; do
    if apt-get -qq install $pkg; then
	echo "Successfully installed $pkg"
    else
	echo "Error installing $pkg"
    fi
done


#Writing physical volume data to disk name                                                                                                                                                                                  
pvcreate $PV_NAME

#creation volume groupe                                                                                                                                                                                                     
vgcreate $VG_NAME  $PV_NAME

sed -e "s/\${name}/${VG_NAME}/" $VOLUME_XML_TEMPLATE > "${VG_NAME}.xml"


#define libvirt pool using volume group                                                                                                                                                                                     
virsh pool-define "${VG_NAME}.xml"
virsh pool-start $VG_NAME
virsh pool-autostart $VG_NAME
virsh pool-info $VG_NAME

#bridge network


