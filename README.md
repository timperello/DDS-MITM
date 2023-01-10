# Factory of the future

ICE-manual

# 1 General setup

The goal of this prototype is to create a setup of a man in the middle attack on a DDS communication. To achieve this several devices have to be configured. This document aims to allow anybody to replicate such an attack. The setup contains a publisher, subscriber, attacker, router, switch and robot. In the second chapter the specific configuration for the machines is listed.

The publisher sends data using DDS, while the subscriber receives data using DDS. The attacker will execute the man in the middle attack and compromise the integrity of the communication. The robot is attached to the subscriber and will receive commands from this machine.

Below the layer 3 design from the technical design is visible to illustrate how the setup is supposed to look. For hardware requirements and other specifications, the technical design can be consulted.


# 2 Specific setup

## 2.1 Switch

When you use the switch for the first time, you need to complete some basic tasks:

1. Reset the switch by pressing the **mode** button for 7 seconds until the lights are on.
2. Connect with the switch by connecting a laptop to any port on the front of the switch using PuTTy and enter the following IP address: **10.0.0.1**

### 2.1.1 Basic configuration

Firstly, we will change the hostname on the switch. Do this by using the following command:

```
hostname fotf_switch
```

After that we will enable a password login for the switch:

```
enable secret fotf2021
```

To configure telnet access, use the following commands:

```
line vty 0 15

password fotf2021

login

exit
```

To configure console access, use the following commands:

```
line console 0

password fotf2021

login

exit
```

### 2.1.2 IP configuration

Here we describe how to assign an IP address to a specific VLAN, and after that configure ports to a VLAN.

First, we interface VLAN 1 with the IP address, 192.168.1.2. Use the following commands to assign an IP address:

```
interface vlan1

ip address 192.168.1.2 255.255.255.0

exit
```

**Assign ports to a VLAN:**
```
configure terminal

interface FastEthernet 0/12

switchport mode access

switchport access vlan 1
```

To interface a range of IP addresses, use the following command:

```
interface range FastEthernet 0 - 18
```

## 2.2 Router

We use one Raspberry Pi as a router. The software we've used is the **OpenWrt** software.

### 2.2.1 Default installation

The installation of OpenWrt on a Raspberry Pi is documented on the website of OpenWrt.

### 2.2.2 Configure client network

Use the following source to connect the router to the Hanz network. DHCP is configured by default, the default DHCP-range is 192.168.1.100-149

### 2.2.3 Access the router

To make a connection with the router, plug-in a network-cable in the switch and your computer. To access the management dashboard, use 192.168.1.1 in your browser while connected to the switch.

## 2.3 Publisher

The publisher will be using a python script to send values to the subscriber. This setup has been tested on a machine with the following setup:

- Debian 11 based operating system
- Python version 3.9.2
- Pip version 20.3.4

To install the RTI Connector for Python the following command can be executed in a terminal:

```
pip3 install rticonnextdds_connector
```

At the time of writing this will install rticonnextdds\_connector version 1.2.0.

Now the file _writer.py_ and _config.xml_ can be copied to the home directory of the publisher. Finally, you can run the publisher by executing the following in the terminal:

```
python3 writer.py
```

Once you see the text

```
Waiting for subscriptions...
```

appear in the terminal the publisher is running and waiting for a subscriber to start writing to.

When the subscriber is found, values are sent to the subscriber and this text appears in the terminal:
```
Writing...
```
and this demonstrates the proper functioning of the script.

To stop the sending of the data, it is necessary to force the script to stop. For that, it is possible to use the command **Ctrl + Z** in the terminal

## 2.4 Subscriber

The subscriber will be using a python script similar to the publisher to receive messages from the publisher. This setup has been tested on a machine with the following setup:

- Debian 11 based operating system
- Python version 3.9.2
- Pip version 20.3.4

Same as the publisher, install the RTI Connector for Python with the following command:

```
pip3 install rticonnextdds_connector
```

At the time of writing this will install rticonnextdds\_connector version 1.2.0.

Next up, you need to install the Universal Robots RTDE C++ Interface. Because we will only be using the Python interface in this setup, you can install this using the following command:

```
pip3 install ur_rtde
```

On the subscriber copy the _reader.py_ and the same _config.xml_ as the publisher to the home directory of the subscriber. In the _reader.py_ change the following line to the correct IP address of the robot:

```
rtde_control.RTDEControlInterface("xxx.xxx.xxx.xxx")
```

Now you can run the subscriber by executing the following in the terminal:

```
python3 reader.py
```

Once you see the text
```
Waiting for publications...
```
appear in the terminal the subscriber is running and waiting for a publisher to start reading to.

You should then see the text 
```
Waiting for data...
```
in the terminal. This means that the subscriber found a publisher. The received data will be displayed in the terminal like this:

```
command: 'rtde_c.moveX([x,x,x,x,x,x])'
```

After being printed, the command is executed.

If the received command does not correspond, this message will be displayed:

```
Unexpected command received
```

## 2.5 Attacker

The attacker will intercept and modify messages sent from the publisher to the subscriber. The setup for this machine is as follows:

- Debian 11 based operating system
- Python version 3.9.2
- Pip version 20.3.4

For intercepting and modifying packets Scapy with the RTPS package will be used. To use the RTPS package we will have to build Scapy from source. This means all existing versions will have to be removed to prevent version conflicts, especially on Kali Linux. This can be done by executing the following commands in the terminal:

```
sudo apt remove python3-scapy

pip3 uninstall scapy
```

To install Scapy from source we first have to install git. Run the following in the terminal to install git:

```
sudo apt install git
```

Then to install Scapy, run the following commands:

```
git clone https://github.com/secdev/scapy.git

cd scapy

sudo python3 setup.py install
```

At the time of writing this will install scapy version 2.5.0rc2.dev16.

Next up, copy the _mitm.py_ to the attacker machine. Open this file using your preferred text editor. In this file change the value of

```
interface = "XXX"
```

to the name of the interface that is connected to the network.

Next, change the values of

```
target1_ip = "xx.xx.xx.xx"

target2_ip = "xx.xx.xx.xx"
```

to the IP addresses of the publisher and subscriber.

If you want the robot to follow a two points path when hacking it, you need to specify

```
global path = True
```

And to change the values of the coordinates you want to send.

```
position1 = "[x,x,x,x,x,x]"

position2 = "[x,x,x,x,x,x]"
```

In case you prefer the robot to just go to a single position, you need to specify

```
global path = False
```

And to change the values of the coordinates you want to send.

```
pos = "[x,x,x,x,x,x]"
```

## 2.6 Encrypted DDS

To implement the encrypted version of the scripts, you need to download the 'Encrypted DDS' scripts and configuration.

These new scripts are using the Python module 'cryptography' to cipher or decipher the data, so you must download it to make them functional.

```
pip3 install cryptography
```

Once you have the scripts and the module, you need to generate a key. For this, you just need to run

```
python key_generator.py
```

In order to send and receive values, each participant needs the same key. This is what allows them to decrypt the data in the same way as it was encrypted. If it is different, you will not be able to recover the data originally sent.

You need to specify in the scripts the location and name of your key file.

```
return open("xxxxx.key", "rb").read()
```

After all of that, the way to run correctly all the scripts is the same which is described in the upper parts. These are the same commands to run the encrypted or unencrypted version.

Take note that the 'Man in the Middle' script will only display encrypted data, because it is unable to decrypt and modify it.