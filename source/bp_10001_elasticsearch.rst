Elastic Search
==============

Introduction
------------
In order to process large amounts of data, for example telemetry data, an object store is typically used. This is true
especially if the data is structured but dynamic, and requires to be indexed and searched. ElasticSearch is a popular
choice as it scalable and fast, and has natively build in some of the features that requires an API to be a TMForum
compliant API.

Purpose
~~~~~~~
The purpose of this document is to describe how Elastic Search can be integrated into the Tachyonic Project as an
option for an object store.

Objective and Scope
~~~~~~~~~~~~~~~~~~~
This document covers some of the concepts of Elastic search, and how it is implemented into the Tachyonic Project.

Integration
-----------
Like all good WEB frameworks, luxon makes use of ORM. It has for example a MySQL Driver that can be used to translate
Models to MySQL tables. To make storage back-ends interchangeable, the aim is to use the same technique of providing
ElastcSearhModel classes that inherits from the Model class. As such, an ``luxon -d`` will create MySQL tables for
SQLModels, and create ElasticSearch indices and their mappings for ElasticSearch Models.

Driver
~~~~~~
An official Elastic Search python library is provided on the Python Package Index [#es]_. This library provides features
such as thread safety and persistent connections, and is used for interface between Tachyonic Projects and Elastic
Search clusters.

Helpers
~~~~~~~
An ElasticSearch helper is supplied, which is a wrapper around the official elasticsearch Class, and obtains credentials
from the project's .ini file's ``[objectstore]`` section. A Basic example:

.. code:: bash

    [objectstore]
    type=ElasticSearch
    host=elasticsearch

"type" has to be ElasticSearch, and to be future proof, the rest of the options are provided as-is to the official
elasticsearch.Elasticsearch() during object initialization. This means any addition initialization parameters
such as authentication credentials can be supplied on a per-implementation basis.

Example usage:

.. code:: python3

    from luxon.helpers.elasticsearch import es

    doc = {
        'from': 0,
        'size': 10000,
        'query': {
            'match_all': {}
        }
    }

    print(es().search(index='my_index', body=doc))


Shards and Replicas
-------------------
Each Elastic Search index is split up into shards, and shards may have replicas for redundancy purposes.

Shards
~~~~~~
These shards are spread across nodes, and when new nodes are added
to the cluster, the shards are moved to be evenly spread again. Once an index has been created, the number of shards
can not be updated. The only way to change the shard size, is by recreating the index (very process intensive task!).
One can also not simply assume the cluster will grow to an indefinite size, and allocate too much shards from
the get go [#mshards]_:

* A shard is a Lucene index under the covers, which uses file handles, memory, and CPU cycles.
* Every search request needs to hit a copy of every shard in the index. That’s fine if every shard is sitting on a
  different node, but not if many shards have to compete for the same resources.
* Term statistics, used to calculate relevance, are per shard. Having a small amount of data in many shards leads to
  poor relevance.

The recommended [#capplan]_ approach to determine the appropriate number of shards and replicas is to:

* Create a cluster consisting of a single server, with the hardware that the user are considering using in production.
* Create an index with the same settings and analyzers that is planned to be used in production,
  but with only one primary shard and no replicas.
* Fill it with real documents (or as close to real as one can get).
* Run real queries and aggregations (or as close to real as one can get).

This setting is of course a per-index setting. As such, the integration is designed to allow the developer to specify
these settings per model, with the ``ElasticSearch`` field method called ``Settings``. An example:

.. code:: python

  from luxon.structs.models.fields.elasticsearchfields import ESFields
  from luxon.structs.models.elasticmodel import ElasticSearchModel

  @register.model()
  class my_index(ElasticSearchModel):
      settings = ESFields.Settings(number_of_shards=1, number_of_replicas=2)

These attributes are passed straight to the "settings" section of the body when the index is created.

For Infinitystone related indexes, the recommendation from the "Designing the perfect elasticsearch cluster the almost
definitive guide" guide of Fred de Villamil [#perfclust]_ is followed:

* 3M documents: 1 shard
* between 3M and 5M documents with an expected growth over 5M: 2 shards.
* More than 5M: int (number of expected documents / 5M +1)

Replicas
~~~~~~~~
The Elasticsearch replication consistency formula is:

``int( (primary + number_of_replicas) / 2 ) + 1``

Going beyond the factor 1 can be extremely useful [#pclustrep]_ when one has a small dataset and a huge amount of
queries. By allocating the whole data set to every node, you can leverage the search thread pools to run much more
queries in parallel. For a fully redundant Tachyonic cluster, a minimum of three servers is typically recommended.
Assuming all three of these servers are also ElasticSearch cluster nodes (or at least three ElasticSearch nodes are
used in any case), the default number_of_replicas is set to two.

Mappings
--------
Luxon models have loads of available different Field types. If an Elastic search index is created without an initial
mapping, ElasticSearch has a dynamic-mapping feature that will create mappings based on the content in the provided
json. Although it is generally good at detecting types, and will for example create an integer mapping for integers in
the json, and boolean mapping for boolean values etc, the auto-mapping might have undesired consequences. For example,
``text`` fields are searchable based on partial matches, while ``kewyord`` fields must match the field entirely.
As such, a means to specify the mapping is provided, via the existing luxon Model fields. This table shows how the
fields are mapped whend indices are created with ``luxon -d``:

=========== ===========
Luxon Field Elastic map
=========== ===========
Text        text
String      keyword
Datetime    date
Boolean     boolean
Integer     integer
BigInt      long
Double      double
Float       float
ip          ip
Json        -
=========== ===========

The Json field should be used when the ElasticSearch dynamic-mapping is required. Basically, mappings for fields of
this type are not created, so that the end-user may supply any custom/unspecified json for this field, and rely on
ElasticSearch's dynamic-mapping feature when the first entry of this field is created. A possible future feature might
be to specify a Luxon Field as a model, instead of a field, and then recurse through the models to create nested
mappings.

Index design
------------
Prior to ElasticSearch 6.0.0 one was able to put objects of different types in the same index. From ElasticSearch
7.0.0 types are depcrecated [#esnotype]_. Since Luxon models for example domain/user are typically completely different
from each other, each model is stored in its own Index.

Development
-----------
The devstack project allows for easy development on Tachyonic modules. Devstack makes use of
docker containers to provide external functionality sych as MariaDB, redis etc. Fortunately there is also an
elasticsearch container available. In devstack it is launched with the following environment variables to start as
a single node:

.. code:: bash

  docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.1.1


Production
----------
When used in Production, it is recommended to run Elastic Search on Bare Metal [#esbm]_. It is recommend to have at
least three nodes in the cluster, with at least 2 master nodes to avoid split brain [#cluster]_. Assume the three
nodes are called node-1, node-2 and node-3, and node-1 and node-2 is configured to be master/data nodes, and node-3 as a
master/http node.

Installing Java
~~~~~~~~~~~~~~~
On all three nodes:

.. code:: bash

    sudo apt-get update
    sudo apt-get install default-jre

Installing Elastic Search
~~~~~~~~~~~~~~~~~~~~~~~~~
On Debian systems the ``apt-transport-https`` package is required. On all three nodes:

.. code:: bash

    wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
    sudo apt-get install apt-transport-https
    echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list
    sudo apt-get update
    sudo apt-get install elasticsearch


Setting up the cluster
~~~~~~~~~~~~~~~~~~~~~~
On each of the nodes, the file to edit is ``/etc/elasticsearch/elasticsearch.yml``

On nodes 1 and 2:

.. code:: bash

    cluster.name: my-cluster
    #provide node name (change node number from node to node).
    node.name: "node-1"
    node.master: true
    node.data: true

    #provide node private ip (change address from node to node).
    network.host: 172.16.0.22
    http.port: 9200

    #detail the private IPs of the nodes:
    discovery.zen.ping.unicast.hosts: ["172.16.0.22", "172.16.0.23","172.16.0.24"]

    #To avoid split brain:
    discovery.zen.minimum_master_nodes: 2


And on node-3:

.. code:: bash

    cluster.name: my-cluster
    #provide node name (change node number from node to node).
    node.name: "node-3"
    node.master: true
    node.data: false

    #provide node private ip (change address from node to node).
    network.host: 172.16.0.24
    http.port: 9200

    #detail the private IPs of the nodes:
    discovery.zen.ping.unicast.hosts: ["172.16.0.22", "172.16.0.23", "172.16.0.24"]

    #To avoid split brain:
    discovery.zen.minimum_master_nodes: 2

Authentication
^^^^^^^^^^^^^^
In order to set up authentication on the service, one needs to set ``xpack.security.enabled: true``. When using a basic
license, this requires inter-node encryption with ``xpack.security.transport.ssl.enabled: true``.
To set up, generate a certificate authority for your cluster. For example, on node-1:

.. code:: bash

    /usr/share/elasticsearch/bin/elasticsearch-certutil ca
    mkdir /etc/elasticsearch/certs
    chown -R root:elasticsearch /etc/elasticsearch/certs/
    cd /usr/share/elasticsearch
    ./bin/elasticsearch-certutil cert --ca elastic-stack-ca.p12 --ip 172.16.0.22 --out /etc/elasticsearch/certs/node-1.p12
    chmod g+r /etc/elasticsearch/certs/node-1.p12

Then edit ``/etc/elasticsearch/elasticsearch.yml``:

.. code:: bash

    xpack.security.enabled: true
    xpack.security.transport.ssl.enabled: true
    xpack.security.transport.ssl.keystore.path: certs/${node.name}.p12
    xpack.security.transport.ssl.truststore.path: certs/${node.name}.p12

Copy the ``elastic-stack-ca.p12`` file to ``/usr/share/elasticsearch`` on node-2 and node-3, and repeat this process
(remembering to use the correct IP address and node name during the creation of the p12 certificate).


Adjusting JVM heap size:
^^^^^^^^^^^^^^^^^^^^^^^^

To ensure Elasticsearch has enough operational leeway, the default JVM heap size (min/max 1 GB) should be adjusted.

As a rule of the thumb, the maximum heap size should be set up to 50% of the RAM, but no more than 32GB
(due to Java pointer inefficiency in larger heaps). Elastic also recommends that the value for maximum and minimum heap
size be identical.

These value can be configured using the Xmx and Xms settings in the ``jvm.options`` file.

On Debian based systems with 4 GB RAM, edit ``/etc/elasticsearch/jvm.options``:

.. code:: bash

    -Xms2g
    -Xmx2g

Disabling swapping:
^^^^^^^^^^^^^^^^^^^

Swapping out unused memory is a known behavior but in the context of Elasticsearch can result in disconnects,
bad performance and in general — an unstable cluster.

To avoid swapping you can either disable all swapping (recommended if Elasticsearch is the only service running on the
server), or you can use mlockall to lock the Elasticsearch process to RAM.

First memory locking must be allowed:

When using the RPM or Debian packages on systems that use systemd, system limits must be specified via systemd.

The systemd service file (``/usr/lib/systemd/system/elasticsearch.service``) contains the limits that are applied by
default.

To override them, add a file called ``/etc/systemd/system/elasticsearch.service.d/override.conf``
(alternatively, run ``sudo systemctl edit elasticsearch`` which opens the file automatically inside the
default editor):

.. code:: bash

    [Service]
    LimitMEMLOCK=infinity

Once finished, run ``sudo systemctl daemon-reload`` command to reload units.

Next, use mlockall to lock the Elasticsearch process to RAM. To do this,
open the Elasticsearch configuration file on all nodes in the cluster
``/etc/elasticsearch/elasticsearch.yml``, and uncomment:

.. code:: bash

    bootstrap.memory_lock: true

and in ``/etc/default/elasticsearch`` set:

.. code:: bash

    MAX_LOCKED_MEMORY=unlimited

Adjusting virtual memory:
^^^^^^^^^^^^^^^^^^^^^^^^^

To avoid running out of virtual memory, increase the amount of limits on mmap counts. In ``/etc/sysctl.conf``, set:

.. code:: bash

    vm.max_map_count=262144

On DEB/RPM, this setting is configured automatically. Verify with:

.. code:: bash

    $ sysctl vm.max_map_count
    vm.max_map_count = 262144

Increasing open file descriptor limit:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Another important configuration is the limit of open file descriptors. Since Elasticsearch makes use of a large amount
of file descriptors, ensure the defined limit is enough otherwise one might end up losing data.

The common recommendation for this setting is 65,536 and higher.

In ``/etc/security/limits.conf``:

.. code:: bash

    elasticsearch - nofile 65536


Finally
^^^^^^^
Then start the elastic-search service.

.. code:: bash

    sudo service elasticsearch start

This takes about a minute or two before all the pocesses has started.

Setup user accounts
^^^^^^^^^^^^^^^^^^^
Because we enabled authentication, all HTTP interactions have to be authenticated. To do this, one needs to
create a user account, and assign a role to it. This is done via the security API. But since even this API requires
authentication, one must first set up the passwords for the built-in user accounts, in order to use that for
the subsequent creation of a new user account. To create the passwords for the built-in accounts:

.. code:: bash

    cd /usr/share/elasticsearch
    ./bin/elasticsearch-setup-passwords interactive

Next, use the ``elastic`` account and password to create a new user.

For example, to create a user called ``tachyonic`` with password of ``T@chy0n1c`` and role ``superuser``:

.. code:: bash

    $ curl -d '{"password" : "T@chy0n1c", "roles" : [ "superuser" ]}' -H "Content-Type: application/json" -X POST 'http://elastic:<password>@172.16.0.22:9200/_security/user/tachyonic'
    {"created":true}

where ``<password>`` is the password entered for the elasticsearch user in the previous step.

Verifying the cluster:
~~~~~~~~~~~~~~~~~~~~~~
.. code:: bash

    curl -XGET 'http://tachyonic:T%40chy0n1c@172.16.0.22:9200/_cluster/health?pretty'
    curl -XGET 'http://tachyonic:T%40chy0n1c@172.16.0.22:9200/_cluster/state?pretty'

Sample output of the first (health) command:

.. code:: json

    {
      "cluster_name" : "my-cluster",
      "status" : "green",
      "timed_out" : false,
      "number_of_nodes" : 3,
      "number_of_data_nodes" : 2,
      "active_primary_shards" : 0,
      "active_shards" : 0,
      "relocating_shards" : 0,
      "initializing_shards" : 0,
      "unassigned_shards" : 0,
      "delayed_unassigned_shards" : 0,
      "number_of_pending_tasks" : 0,
      "number_of_in_flight_fetch" : 0,
      "task_max_waiting_in_queue_millis" : 0,
      "active_shards_percent_as_number" : 100.0
    }

Redundancy
~~~~~~~~~~
With three nodes in the cluster, the setup can be made highly available with haproxy. Example config snippet
for ``/etc/haproxy/haproxy.conf`` on node 1:

.. code:: bash

    listen elasticsearch
        bind 172.16.0.22:9292
            balance source
            mode tcp
            timeout client 10800s
            timeout server 10800s
            option tcpka
            server node-1 172.16.0.22:9200 check
            server node-2 172.16.0.23:9200 check
            server node-3 172.16.0.24:9200 check

Troubleshooting
---------------
If the service elasticsearch service fails after starting, consult the ``/var/log/elasticsearch/my-cluster.log``
log file.

References
----------

.. rubric:: References

.. [#es] `<https://pypi.org/project/elasticsearch/>`_
.. [#mshards] `<https://www.elastic.co/guide/en/elasticsearch/guide/2.x/kagillion-shards.html>`_
.. [#capplan] `<https://www.elastic.co/guide/en/elasticsearch/guide/2.x/capacity-planning.html>`_
.. [#perfclust] `<https://thoughts.t37.net/designing-the-perfect-elasticsearch-cluster-the-almost-definitive-guide-e614eabc1a87>`_
.. [#pclustrep] `<https://thoughts.t37.net/designing-the-perfect-elasticsearch-cluster-the-almost-definitive-guide-e614eabc1a87#e70b>`_
.. [#esbm] `<https://thoughts.t37.net/designing-the-perfect-elasticsearch-cluster-the-almost-definitive-guide-e614eabc1a87#d863>`_
.. [#esnotype] `<https://www.elastic.co/guide/en/elasticsearch/reference/6.0/removal-of-types.html>`_
.. [#cluster] `<https://logz.io/blog/elasticsearch-cluster-tutorial>`_


Author
------

Dave Kruger
Email: davek@tachyonic.org

