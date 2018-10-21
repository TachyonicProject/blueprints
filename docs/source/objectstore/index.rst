============
Object Store
============

------------
Introduction
------------

The Tachyonic Project [#tp]_ includes an object store. It is highly available, distributed, eventually consistent object/blob store. Tachyonic projects can use it store lots of data efficiently, safely, and cheaply.

You create, modify, and get objects and metadata by using the Object Storage API, which is implemented as a set of Representational State Transfer (REST) web services.

To assert your right to access and change data in an account, you identify yourself to Object Storage by using an authentication token. To get a token, you present your credentials to an Identity service (Infinitystone).

The Object Storage system organizes data in a hierarchy, as follows:

 * Account. Represents the top-level of the hierarchy.

   The account defines a namespace for containers. A container might have the same name in two different accounts.

   In the Tachyonic environment, account is synonymous with a tenant.

 * Container. Defines a namespace for objects. An object with the same name in two different containers represents two different objects. You can have any number of containers within an account.

 * Object. Stores data content, such as documents, images, and so on.

The account, container, and object hierarchy affects the way you interact with the Object Storage API. Specifically, the resource path reflects this structure and has this format:

 /v1/{account}/{container}/{object}

----------------------
Architectural Overview
----------------------

Data Distribution
~~~~~~~~~~~~~~~~~

“Consistent Hashing” is a term used to describe a process where data is distributed using a hashing algorithm to determine its location. Using only the hash of the id of the data you can determine exactly where that data should be. This mapping of hashes to locations is usually termed a “ring”.

Probably the simplest hash is just a modulus of the id. For instance, if all ids are numbers and you have two machines you wish to distribute data to, you could just put all odd numbered ids on one machine and even numbered ids on the other. Assuming you have a balanced number of odd and even numbered ids, and a balanced data size per id, your data would be balanced between the two machines.

Since data ids are often textual names and not numbers, like paths for files or URLs, it makes sense to use a “real” hashing algorithm to convert the names to numbers first. Using MD5 for instance and modulus, we have some form of sharding algorithm.  Another benefit of using a hashing algorithm like MD5 is that the resulting hashes have a known even distribution, meaning your ids will be evenly distributed without worrying about keeping the id values themselves evenly distributed.


Tenant Container Index
~~~~~~~~~~~~~~~~~~~~~~
Purely used to keep track of all containers stored in for a tenant. SQLLite is used for storing these and data on a per Tenant database.


Container Object Index
~~~~~~~~~~~~~~~~~~~~~~
Purely used to keep track of all objects stored in container for a tenant. SQLLite is used for storing these and data on per Tenant Container database.


Rings
~~~~~~~~~~~~~~~~~~~~~~
The purpose of a Ring is to manage the storage cluster and data distribution.

There are two rings:

   * Per Tenant / Container Index Locations
   * Object Store Ring.

Rings identify the location and replica locations for nodes based on consistant hashing algorithm. All nodes will be used for storage.

Rings have snapshots to locate old locations of storage, however only 6 snapshots are kept. So in short do not rebuild the ring more than 6 times untill all data on all objects are completely rebalanced/distributed. The purpose of the snapshots is to ensure data is always availible. 

To ensure data is replicated in the most redundant fashion there are zones for nodes. Zones are redundant locations or group of servers.

Replicas are the amount of duplicated objects to store on different zones. If there are more replicas than zones or nodes, Then some nodes or zones will be re-used. However nodes will only be re-used if they have additional redundant drives.

Ring builder/manager utility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This is a command line tool, used via shell on any of the object stores.

The Ring administrator provides the ability to:

   * Add / Update / Remove nodes.
   * Add / Remove Storage Drives to nodes.
   * Add / Rename / Remove zones.
   * A Weight can be used to determine distribution of data onto a node.
   * Build / Rebalance the Ring. This effetively rebalances distribution of objects and container databases.
   * Distribute updated rings to Katalog nodes via REST API.
   * Versioning of Rings. Incrementing Number on all operations.

Nodes are actual object storage server which may contain several drives for storage.

Ring daemon
~~~~~~~~~~~
The ring daemon runs on a local unix socket. Since loading a Ring on while processing a request in WSGI is vastly duplicted memory usage and load times, the ring daemon provides more effeciant mechanisem.

If it detected a new ring stored locally, it will reload the Ring topology. On every Ring query it will valide its Ring topology. Updating ring information is distributed via the endpoint API.

The ring data is stored in Python pickled format. Far more effeciant than using JSON/XML.

The Ring Daemon provides two key features via its unix socket API:

   * Query Locations known for {tenant_id} container databases.
   * Query Locations known for {tenant_id}/{container}/{object} objects.
   * The version of Ring is returned with all queries. 
   * Query Ring Version

Object daemon
~~~~~~~~~~~~~
The Object Server is a very simple blob storage server that can store, retrieve and delete objects stored on local devices. Objects are stored as binary files on the filesystem with metadata stored in the file’s extended attributes (xattrs). This requires that the underlying filesystem choice for object servers support xattrs on files. Some filesystems, like ext3, have xattrs turned off by default.

Each object is stored using a path derived from the object name’s hash and the operation’s timestamp. Last write always wins, and ensures that the latest object version will be served.

Tenant container daemon
~~~~~~~~~~~~~~~~~~~~~~~

Replicator daemon
~~~~~~~~~~~~~~~~~

RestAPI
~~~~~~~


.. [#tp] The Tachyonic Project is a Multi-Tenant Multi-Tiered Eco System that was build for Service Providers. For more information, see `<http://tachyonic.org>
