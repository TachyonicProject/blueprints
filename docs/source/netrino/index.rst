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

During element creation, a UUID is generated, and an element name must be supplied. The only compulsory field is the device name, which has to be
unique, in order to prevent the confusion which would most likely ensue when it isn't. The following fields are
optional:

* Tags
* Region
* Parent element UUID
* Periodic scanning enabled, and if so the interval.
* After-provisioning scanning enabled

Some drivers store additional information about elements. The SNMP driver for example will store the version and
community string required to communicate with the device, while the SSH driver stores username and password or key.
Some drivers also store :ref:`resources <resources>` associated with the element.

Discovering of new Elements
---------------------------
Netrino also provides the ability for the bulk addition of elements. When a subnet is supplied during a creation
request instead of a single IP address, it will iterate through the ip addresses in the subnet
and attempt to connect to each one.
When a successful communication attempt has been made, it is the task of the driver to add the element
(or update if it already exists), include itself in the list of available drivers for the element,
and update all other relevant tables such as resource tables as needed.

Removal of Elements
===================
Elements can be completely removed from the database. When this happens, all resources tied to it becomes available
for usage again.


.. _update:

Updating of Elements
====================
Netrino assumes it is not the only orchestrator of the elements and thus allows for element configuration updates
outside of its scope. This gives rise to the requirement that elements have to be regularly "scanned" for changes in
configuration and resource usage. Elements can be configured to be scanned at regular intervals, or every time after
Netrino has updated its configuration or both. The default is not to be scanned.

Elements can be updated on an ad-hoc basis as well. This could for example be usefull to run after an element's IP
 address is updated.

Drivers
=======
As mentioned, the driver used for communicating with an element, is a python module. The driver can have arbitrary
methods available, but for use with Netrino, must supply the following methods:

* discover - adds device if successful communication attempt has been made.
* create - adds device without attempting to connect (use case: device not live yet)
* configure - updates device configuration.
* remove - removes this driver from the list of available drivers for the elements.
* update - run a full scan on the device in order to update Netrino's view of its configuration and resource usage.

.. _resources:

----------------
Resource Manager
----------------
In order to provide a service, one typically requires resources. For example, this could be things like IP address,
VLAN number, device port or BGP community such as a route-target. These are collectively referred to as resources.

Netrino has a built-in resource manager that caters both for green fields and brown fields.

When creating a resource pool, it is given a type (eg. IPv4) and a range. The actual resource usage is stored in a
different table that references this pool. In the brown-fields scenario, whenever an
element is :ref:`updated <updated>`, the resource usage is updated.

When designing a :ref:`service <services>`, the chosen YANG models are scanned for type definitions. Certain types can
be linked to resource pools. For example, the `RFC 6991 <https://tools.ietf.org/html/rfc6991>`_ type definition of
``ipv4-address`` is linked to IPv4 resource pools. As such, the resource pools can be associated to those entries in
the YANG models so that the entries can be automatically assigned from the next available resource in the pool when a
Service is requested.

Resource pools thus have an optional associated list of YANG type definitions.

Resource pools can be globally significant (e.g. public IPv4's) or element-significant (eg. VLANS on a switch). Unless
specified otherwise, global is assumed. If locally significant is specified during the cration/updating of a resource
pool, then the element or element tag has to be specified that this resource pool is linked to.

----------------
Service Desginer
----------------

YANG
====
Netrino makes use of `YANG <https://tools.ietf.org/html/rfc7950>`_ models to define Services. Although YANG was designed
along side NETCONF, it can be used for any arbitrary modelling since it can be serialized into popular API notation
formats such as JSON or XML.

This means not only does Netrino support your favourite vendor out of the box by loading its YANG models (if it already
supports NETCONF), but you can even make provision for ones that don't by creating the YANG model and driver for it
yourself.

.. _services:

Service Templates
=================
In order for Netrino to provision a service, it has to be told what the service comprises of. The Service designer
provides to the operator the opportunity to do just this.

When designing a service, the operator specifies the YANG model or models to use for the service. Each model can also
be linked to an element or element tag. In case linked to an element tag, the requester of the service has to specify
which of those elements is to be used for this particular model of the service. (Choosing an element that does not have
the associated tag will result in a failure of the service request creation.)

By default, the netconf driver will be used for communication with the element, but this can be overwritten when
designing the service. The JSON data sent in the request for creation of the service, must contain the device ID and
data matching the YANG model for each model.

Some drivers do not make use of netconf as the underlying communication protocol. When Services are designed for these,
we still specify a YANG model, but specify a different driver to be used. Netrino comes with a couple of built-in YANG
modes for its built-in drivers, such as ansible and SNMP. These YANG models are purely used for validation during
creation of the :ref:`service request`, the actual data sent is passed to the driver directly if successful.

.. _service_request:

----------------
Service Requests
----------------
This is one of the main reasons for Netrino's existence. A service request is the marriage of a service to a customer,
which inevitably also involves configuration update on one or more elements. If customer X wants service Y, create
a service request on Netrino.

The customer is automatically selected as the current tenant in the Infinitystone scope, and the service template
must explicitly be specified. Once the service template is known, the additional fields is dictated by the YANG models
in the service template. If the data in the service request can not be parsed for whatever reason (inluding invalid
syntax, required field(s) missing or resource depleted) the service request is not created. On the other hand, if all
information was supplied correctly, the service request is created immediately, and the user may reference it at any time
to get an update on its status.

During the creation of a service request, Netrino will auto-populate resources from the next available in the pool
where required. The moment it does this, it will immediately remove the resource as being available from the pool,
in order to prevent a race condition. If spare resources in the pool has been depleted, an exception is raised.

.. rubric:: Footnotes

.. [#tp] The Tachyonic Project is a Multi-Tenant Multi-Tiered Eco System that was build for Service Providers. For more information, see `<http://tachyonic.org>`_