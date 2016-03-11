==================================================================================

Prerequisite for this project :-
	1. Python Flask
	2. Virtual Machine Manager
	3. SQLite
	
==================================================================================

Command to run :-
	python server.py <physical_machine_list_file> <image_location_file> <flavour_file>
Ex. python server.py pm_file.txt image_file.txt json_file.json

==================================================================================

Running Instruction :-
	a. Vmid or pmid :- name or id of vm
	b. Instance_type :- Starts from 0
	c. Image Id :- Starts from 100
	d. Place the image file at desktop
	e. Replace the path in image_file.txt to your path to image file
	f. I have also uploded a small image file of cirros OS 

==================================================================================

Configuration for Removing authentication from libvirt/kvm :-
	Replace this two files to the files present in config directory to the files present in below path
		a.  /etc/libvirt/libvirtd.conf
		    /etc/default/libvirt-bin

		b.  Restart libvirt : /etc/init.d/libvirt-bin restart

==================================================================================