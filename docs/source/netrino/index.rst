============================================
Netrino, the TachyonicProject's Orchestrator
============================================

.. note:: This is still a work in progress.


------------
Introduction
------------

The Tachyonic Project [#tp]_ includes an orchestrator, called Netrino. Netrino is capable of orchestration on many different
device types. Some directly, and others via existing orchestrators of those devices. Hence the reference of
"Orchestrator of Orchestrators".

One of the end goals is for the system to do the life cycle management of services.

These services could be anything, from simple services like email, SIP or VPN services, to more complex ones like
MPLS Layer3 VPNs or Metro Ethernet.

For this purpose, Netrino has multiple roles. It has an Element manager, Resource manager, Templating engine and Service
designer.

.. image:: /_static/img/NetrinoOverview.png

This page contains the blueprint for the design of Netrino.


---------------
Element Manager
---------------

Netrino has two reasons for communicating with devices. One is for information gathering, the other for configuring.
Different devices have different methods and protocols available for these purposes. The aim for Netrino is to be
as flexible as possible (thus allowing multiple methods to communicate to devices, and providing the option to choose
which) and as extensible as possible (allowing for future-proofing by catering for the seamless addition
of new methods).

The devices on which Netrino has to orchestrate services, are referred to as elements. Netrino needs to store a list
of these elements, so that it can make elements available when services are to be provisioned on them.

Typically, elements will have an IP address associated, which is used for communicating with the device. However, it is
foreseen that Netrino is to know about devices which it can not communicate with. An example would be a cabinet in which
devices are mounted. For this reason, an IP address is not a required value when storing an element's details.

Elements should have at least a name. For servers and network devices like routers, this would eg. be the hostname.
The primary key used to reference elements is a UUID, which allows one to change an element's IP and/or hostname without
losing any back references.

Netrino uses drivers to communicate with devices. These drivers are python modules. The drivers register themselves with
Netrino to make their presence known. Netrino comes with a couple of built-in drivers, and also provides the ability to
easily add new drivers. As mentioned previously, an element may have more than one driver associated with it. The
specific driver to use for communication during a particular request, is to be explicitly referenced during the API
call for that request.

Elements may have a parent element associated with them. For Example, a server might have the UUID of a cabinet as its
parent element. The cabinet in return, might have a data center room's UUID as its parent element reference.
This of course implies that elements may have one or more children.

Grouping
========

InfinityStone caters for domains and regions. Netrino's elements may belong to a region, but not to a domain. The
reason for this is that even when working inside a scoped session, all elements must still be available for service
orchestration. For this reason all elements wil always "exist" in the global Infinitystone scope.

Typically one could have more than one Netrino installation, and they may have jurisdiction over
different regions. For High Availability purposes, a region may have more than one Netrino instance as well.

Inter region orchestration happens as follows: When a Netrino instance receives a request to provision on an element
that is in another region, it will forward the request to the Netrino endpoint in that region.

Elements can belong to different device groups as well, purely for convenience sake. This is done by means of tagging.
This allows one to tag devices by category, purpose, or whatever grouping is useful.


Addition of New Elements
========================
When a new element is added to Netrino, one may specify the drivers available for communication with the device.
If no drivers are associated with the device, communication with it wil not be possible.

During element creation, a UUID is generated, and an element name must be supplied. Tags, region, and parent element
UUID could all be supplied, but are not compulsory. The only compulsory field is the device name, which has to be
unique, in order to prevent the confusion which would most likely ensue when it isn't.

Some drivers store additional information about elements. The SNMP driver for example will store the version and
community string required to communicate with the device, while the SSH driver stores username and password or key.
Some drivers also store :ref:`resources <resources>` associated with the element.

Discovering of new Elements
---------------------------
Netrino also provides the capability to bulk-add elements. When a subnet is supplied during a creation or request, it
will iterate through the ip adresses in the subnet, and attempt to connect to each one. When a successful communication
attempt has been made, the element will be added (or updated if already exists), the driver used will be added in the
list of available drivers for the element, and all other relevant tables will be updated.


.. _resources:

Resources
=========
In order to provide a service, one typically requires resources. For example, this could be things like IP address,
VLAN number, device port or BGP community such as a route-target. These are collectively referred to as resources.

Netrino has a built-in resource manager that caters both for green fields and brown fields.


.. rubric:: Footnotes

.. [#tp] The Tachyonic Project is a Multi-Tenant Multi-Tiered Eco System that was build for Service Providers. For more information, see `<http://tachyonic.org>`_