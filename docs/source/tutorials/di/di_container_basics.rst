#####################################
Dependency Injection container basics
#####################################

A dependency injection container associates contracts (interfaces, protocols) with their concrete implementations. Interactions with the container can be divided into two categories: registration and resolution. While registration usually precedes resolution, it's necessary to understand what happends during resolution before beginning to discuss the registration stage.

**********
Resolution
**********

The ultimate goal of the container is to provide instances of objects that satisfy the requested contract. We will call such instances *beans*, and the process of obtaining such instances from a container --- *resolution*. In some places, we will highlight that we are talking about the bean and not its type by calling it a *bean instance* instead.

During resolution, the container attempts to look up registrations for the requested contract, and construct or retrieve an appropriate bean. Meanwhile, the code that initiated (requested) the bean resolution needs not know how the bean was constructed, or even how the contract will be fulfilled. This ensures loose coupling and makes your assumptions about the requested objects more explicit.

Let's take a look at an example, without going into much detail concerning how the container is configured:

.. code-block:: python

    from abc import ABC, abstractmethod
    from grundzeug.container import IContainer, Container
    from grundzeug.container.registrations import RegistrationTypes

    class Contract(ABC):
        @abstractmethod
        def foo():
            raise NotImplementedError()

    class FirstImplementation(Contract):
        def foo():
            ...

    ...

    container = Container()
    
    # Configure the container to resolve an instance 
    # of `FirstImplementation` when `Contract` is requested.
    configure_container(container)

    # We do not care how the contract is fulfiled, 
    # but `bean` will be an instance of `FirstImplementation`
    # in this case.
    bean = container.resolve[Contract]()

    bean.foo()

Container hierarchies
=====================

Grundzeug, being a hierarchical container, supports overriding registrations in child containers. We can demonstrate the hierarchical nature of the container by extending our current example:

.. code-block:: python

    class SecondImplementation(Contract):
        def foo():
            ...

    ...

    child_container = Container(parent=container)

    # Child containers inherit registrations.
    bean_from_child = child_container.resolve[Contract]()
    assert isinstance(bean_from_child, FirstImplementation)

    # Configure the child container to resolve an instance 
    # of `SecondImplementation` when `Contract` is requested.
    configure_child_container(child_container)
    
    # The bean resolved from the child container will be an 
    # instance of `SecondImplementation`, while the bean
    # resolved from the root container will still be an 
    # instance of FirstImplementation.
    bean = container.resolve[Contract]()
    bean_from_child = child_container.resolve[Contract]()
    assert isinstance(bean, FirstImplementation)
    assert isinstance(bean_from_child, SecondImplementation)

Basic dependency injection
===================================

So far, we've been treating our container as a *service locator*. While calling ``resolve`` is sometimes necessary, it should be a rare occurance in a high-quality code-base. Instead, we should aim to automatically *inject* dependencies into places where they are required.

Let's take a look at a contrived example:

.. code-block:: python

    from grundzeug.container.di import Inject

    def perform_foo(greeting: str, contract_impl: Inject[Contract]) -> None:
        contract_impl.foo()
        print(greeting)

    # Partially apply perform_foo using beans from the 
    # container, binding a bean that satisfies 
    # Contract to contract_impl.
    injected_func : Callable[[str], None] = container.inject(perform_foo)
    # We can still pass arguments to an injected function!
    injected_func("hello world")

.. note::

    ``Inject[Contract]`` is just a shorthand for PEP 593 ``Annotated[Contract, InjectAnnotation[Contract]]``.

By calling ``container.inject`` on ``perform_foo``, we have essentially performed ``injected_func = functools.partial(perform_foo, contract_impl=container.resolve[Contract]())``.

************
Registration
************

Let's set aside resolution for now and talk about the registration stage, which defines where the beans come from, where they are stored, and when they should be discarded.

Each container has a list of *registrations* associated with it. Each registration is responsible for constructing and keeping track of bean instances associated with a specified contract. Different *registration types* implement different bean lifecycle management strategies, giving us the ability to, for instance, create a new bean each time the contract is requested.

The process of adding a new registration to a container is called *bean registration*.

Providing bean instances to registrations
=========================================


Instance registration
---------------------

Instance registrations are a special (trivial) case, since the user must provide the actual bean that will be resolved each time the associated contract is requested from the container (or one of its descendants):

.. code-block:: python


    def configure_container(container: IContainer):
        bean = FirstImplementation()
        container.register_instance[Contract](bean)

        assert id(container.resolve[Contract]()) == id(bean)

While sometimes useful, instance registration "misses the point" of having a dependency injection container, because it requires us to explicitly construct the bean, passing its dependencies manually.

Type registration
-----------------

The most common way to register a bean definition is to provide the bean's type. When a new instance of the bean is required, Grundzeug will simply call the type's constructor, injecting any dependencies in the process.

To demonstrate this, let's create a third implementation of ``Contract``, which depends on some dependency that satisfies ``DependencyContract``:

.. code-block:: python

    class ThirdImplementation(Contract):
        def __init__(dependency: Inject[DependencyContract]):
            ...

        def foo():
            ...

    def configure_container(container: IContainer):
        # Configure an implementation for DependencyContract.
        add_dependency_impl_to_container(container)
        ...
        container.register_type[Contract, ThirdImplementation]()

If we configure the container as specified above, the container will create an instance of ``ThirdImplementation`` the first time ``Contract`` is requested, injecting its dependencies, and keep returning the same instance each time the contract is requested. Moreover, every child container will return the same instance unless a superseding bean registration is provided.

Sometimes, the contract matches the implementation, in which case you may use the shorthand syntax:

.. code-block:: python

    # Register FirstImplementation to satisfy FirstImplementation
    container.register_type[FirstImplementation]()



Factory registration
-----------------------

Factory injection behaves similarly to type registration, except that you provide a factory function instead of a type:

.. code-block:: python

    def configure_container(container: IContainer):
        def create_first_implementation():
            return FirstImplementation()
        container.register_factory[Contract](create_first_implementation)

When the factory is called, it also receives any required dependencies. The code used to construct the bean looks roughly like this:

.. code-block:: python

    return container.inject(factory)()

Registration types
==================

Container
---------

When registering a type or a factory, the default behaviour is to create the bean on first request, and then return the same instance for any subsequent requests. This registration type is great for replacing unnecessary singletons:

.. code-block:: python
    
    # The following two calls to register_type are equivalent:
    container.register_type[Contract, FirstImplementation]()
    container.register_type[Contract, FirstImplementation](
        registration_type=RegistrationTypes.Container
    )

    assert id(container.resolve[Contract]()) == id(container.resolve[Contract]())
    assert id(container.resolve[Contract]()) == id(child_container.resolve[Contract]())
    
Hierarchical
------------

Sometimes, it is desirable for descendant containers to have their own bean instances without any additional configuration. The ``Hierarchical`` registration type maintains separate bean instances for each descendant container, instantiating them only after they have been requested.

.. code-block:: python
    
    container.register_type[Contract, FirstImplementation](
        registration_type=RegistrationTypes.Hierarchical
    )

    assert id(container.resolve[Contract]()) == id(container.resolve[Contract]())
    assert id(container.resolve[Contract]()) != id(child_container.resolve[Contract]())

Transient
---------

In some cases, the bean should be instantiated on each request. The ``Transient`` registration type provides just that: it calls the configured factory on each resolution, each time giving us a new bean instance (assuming that the factory returns a new bean instance on each call).

.. code-block:: python
    
    container.register_type[FirstImplementation](
        registration_type=RegistrationTypes.Transient
    )

    assert id(container.resolve[Contract]()) != id(container.resolve[Contract]())


Named beans
===============

In addition to contracts, there is a secondary mechanism for identifying beans in Grundzeug. You may register multiple
beans to contracts under different names:

.. code-block:: python


    def configure_container(container: IContainer):
        first_bean = FirstImplementation()
        second_bean = FirstImplementation()
        container.register_instance[Contract](first_bean, bean_name="first_bean")
        container.register_instance[Contract](second_bean, bean_name="second_bean")

        assert id(container.resolve[Contract](bean_name="first_bean")) == id(first_bean)
        assert id(container.resolve[Contract](bean_name="second_bean")) == id(second_bean)