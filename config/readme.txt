Removing authentication from libvirt/kvm...

Replace the attached two files found in the following location...
/etc/libvirt/libvirtd.conf
/etc/default/libvirt-bin

then run this command to restart libvirt : /etc/init.d/libvirt-bin restart

open kvm connection using "qemu+tcp://127.0.0.1/system" url..