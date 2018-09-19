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

Proxy Server (Katalog)
~~~~~~~~~~~~~~~~~~~~~~

The Proxy Server is responsible for tying together the rest of the Swift architecture. For each request, it will look up the location of the account, container, or object in the ring (see below) and route the request accordingly.

A large number of failures are also handled in the Proxy Server. For example, if a server is unavailable for an object PUT, it will use a redundant server and route there instead.

When objects are streamed to or from an object server, they are streamed directly through the proxy server to or from the user – the proxy server does not spool them.

The katalog servers use a sql cluster for storing list of objects. However the list is not used ot resolve the location of the object.

Object Server (Kiloquad)
~~~~~~~~~~~~~~~~~~~~~~~~

The Object Server is a very simple blob storage server that can store, retrieve and delete objects stored on local devices. Objects are stored as binary files on the filesystem with metadata stored in the file’s extended attributes (xattrs). This requires that the underlying filesystem choice for object servers support xattrs on files. Some filesystems, like ext3, have xattrs turned off by default.

Each object is stored using a path derived from the object name’s hash and the operation’s timestamp. Last write always wins, and ensures that the latest object version will be served.

Replication Service
~~~~~~~~~~~~~~~~~~~

Replication is designed to keep the system in a consistent state in the face of temporary error conditions like network outages or drive failures.

The replication processes compare local data with each remote copy to ensure they all contain the latest version. Object replication uses a hash list to quickly compare subsections of each partition

Replication updates are push based. For object replication, updating is just a matter of rsyncing files to the peer. Account and container replication push missing records over HTTP.

The replicator also ensures that data is removed from the system. When an item (object, container, or account) is deleted, a tombstone is set as the latest version of the item. The replicator will see the tombstone and ensure that the item is removed from the entire system.

Data Distribution
~~~~~~~~~~~~~~~~~

“Consistent Hashing” is a term used to describe a process where data is distributed using a hashing algorithm to determine its location. Using only the hash of the id of the data you can determine exactly where that data should be. This mapping of hashes to locations is usually termed a “ring”.

Probably the simplest hash is just a modulus of the id. For instance, if all ids are numbers and you have two machines you wish to distribute data to, you could just put all odd numbered ids on one machine and even numbered ids on the other. Assuming you have a balanced number of odd and even numbered ids, and a balanced data size per id, your data would be balanced between the two machines.

Since data ids are often textual names and not numbers, like paths for files or URLs, it makes sense to use a “real” hashing algorithm to convert the names to numbers first. Using MD5 for instance and modulus, we have some form of sharding algorithm.  Another benefit of using a hashing algorithm like MD5 is that the resulting hashes have a known even distribution, meaning your ids will be evenly distributed without worrying about keeping the id values themselves evenly distributed.

.. [#tp] The Tachyonic Project is a Multi-Tenant Multi-Tiered Eco System that was build for Service Providers. For more information, see `<http://tachyonic.org>
