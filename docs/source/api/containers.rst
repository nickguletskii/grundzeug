==========
Containers
==========

----------
Containers
----------


The principal object in the Grundzeug Dependency Injection container is the :py:class:`~grundzeug.container.IContainer`
and its default implementation, :py:class:`~grundzeug.container.Container`:

IContainer
----------

.. autoclass:: grundzeug.container.IContainer
   :members:
   :undoc-members:
   :inherited-members:


Container
---------

.. autoclass:: grundzeug.container.Container
   :members:
   :undoc-members:
   :inherited-members:

---------
Injectors
---------

Instead of injecting the container into your functions and classes, inject :py:class:`~grundzeug.container.Injector`
to explicitly state that the container is not going to be mutated:

Injector
--------

.. autoclass:: grundzeug.container.Injector
   :members:
   :undoc-members:
   :inherited-members:

The default implementation as returned by the containers is the :py:class:`~ContainerInjector`:


ContainerInjector
-----------------

.. autoclass:: grundzeug.container.ContainerInjector
   :members:
   :undoc-members:
   :inherited-members:

-----------------------
Container registrations
-----------------------

ContainerRegistration
---------------------

.. autoclass:: grundzeug.container.ContainerRegistration
   :members:
   :undoc-members:
   :inherited-members:

RegistrationTypes
-----------------

.. autoclass:: grundzeug.container.registrations.RegistrationTypes
   :members:
   :undoc-members:
   :inherited-members:

InstanceContainerRegistration
-----------------------------

.. autoclass:: grundzeug.container.registrations.InstanceContainerRegistration
   :members:
   :undoc-members:
   :inherited-members:

ContainerFactoryContainerRegistration
-------------------------------------

.. autoclass:: grundzeug.container.registrations.ContainerFactoryContainerRegistration
   :members:
   :undoc-members:
   :inherited-members:

TransientFactoryContainerRegistration
-------------------------------------

.. autoclass:: grundzeug.container.registrations.TransientFactoryContainerRegistration
   :members:
   :undoc-members:
   :inherited-members:

HierarchicalFactoryContainerRegistration
----------------------------------------

.. autoclass:: grundzeug.container.registrations.HierarchicalFactoryContainerRegistration
   :members:
   :undoc-members:
   :inherited-members:

----------
Exceptions
----------

ContainerAlreadyHasRegistrationError
------------------------------------

.. autoclass:: grundzeug.container.exceptions.ContainerAlreadyHasRegistrationError
   :members:
   :undoc-members:
   :inherited-members:

ResolutionFailedError
---------------------

.. autoclass:: grundzeug.container.exceptions.ResolutionFailedError
   :members:
   :undoc-members:
   :inherited-members:

----------------------
Common data interfaces
----------------------

RegistrationKey
---------------

.. autoclass:: grundzeug.container.RegistrationKey
   :members:
   :undoc-members:
   :inherited-members:

--------------
Helper classes
--------------

The following interfaces and classes are used to implement the indexing syntax used in the
``~grundzeug.container.IContainer``.


GetBeanProtocol
---------------

.. autoclass:: grundzeug.container.GetBeanProtocol
   :members:
   :undoc-members:
   :inherited-members:

IContainerResolveIndexer
------------------------

.. autoclass:: grundzeug.container.IContainerResolveIndexer
   :members:
   :undoc-members:
   :inherited-members:

RegisterInstanceProtocol
------------------------

.. autoclass:: grundzeug.container.RegisterInstanceProtocol
   :members:
   :undoc-members:
   :inherited-members:

IContainerRegisterInstanceIndexer
---------------------------------

.. autoclass:: grundzeug.container.IContainerRegisterInstanceIndexer
   :members:
   :undoc-members:
   :inherited-members:

RegisterFactoryProtocol
-----------------------

.. autoclass:: grundzeug.container.RegisterFactoryProtocol
   :members:
   :undoc-members:
   :inherited-members:

IContainerRegisterFactoryIndexer
--------------------------------

.. autoclass:: grundzeug.container.IContainerRegisterFactoryIndexer
   :members:
   :undoc-members:
   :inherited-members:

RegisterTypeProtocol
--------------------

.. autoclass:: grundzeug.container.RegisterTypeProtocol
   :members:
   :undoc-members:
   :inherited-members:

IContainerRegisterTypeIndexer
-----------------------------

.. autoclass:: grundzeug.container.IContainerRegisterTypeIndexer
   :members:
   :undoc-members:
   :inherited-members:

ContainerResolveIndexer
-----------------------

.. autoclass:: grundzeug.container.ContainerResolveIndexer
   :members:
   :undoc-members:
   :inherited-members:

ContainerRegisterInstanceIndexer
--------------------------------

.. autoclass:: grundzeug.container.ContainerRegisterInstanceIndexer
   :members:
   :undoc-members:
   :inherited-members:

ContainerRegisterFactoryIndexer
-------------------------------

.. autoclass:: grundzeug.container.ContainerRegisterFactoryIndexer
   :members:
   :undoc-members:
   :inherited-members:

ContainerRegisterTypeIndexer
----------------------------

.. autoclass:: grundzeug.container.ContainerRegisterTypeIndexer
   :members:
   :undoc-members:
   :inherited-members:
