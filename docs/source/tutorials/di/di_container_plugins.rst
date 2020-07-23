######################################
Dependency Injection container plugins
######################################

Grundzeug containers can be extended using container resolution plugins. Container resolution plugins can handle
specific types of contracts and implement their own bean resolution logic.

*****************************
Adding plugins to a container
*****************************

To add a plugin to a container hierarchy, call :py:meth:`~grundzeug.container.interface.IContainer.add_plugin` on the
root container:

.. code-block:: python

    container = Container()
    container.add_plugin(ContainerConverterResolutionPlugin())

.. warning::

    Plugins are shared by the whole container hierarchy! This means that any descendant container is always going to
    have the same list of plugins as the container itself!

.. note::

    Plugin order matters. The first plugin to be added to the container will be the last plugin to be executed during
    registration and resolution. You may review the order of the plugins by inspecting the ``plugins`` field on the
    container, which contains a list of plugins that were added to this container hierarchy in the order that they will
    be executed (i.e. in reverse order to the order they were added in).

****************
Built-in plugins
****************


ContainerSingleValueResolutionPlugin
====================================

The default bean resolution logic that was demonstrated in the dependency container basics and dependency injection
tutorials is provided by the
:py:class:`~grundzeug.container.plugins.ContainerSingleValueResolutionPlugin`
plugin. In other words, this plugin provides the default bean resolution logic that you may see in other IoC containers
such as Unity.

This plugin is registered in containers by default and acts as the fallback for any bean registrations.

ContainerBeanListResolutionPlugin
=================================

The :py:class:`~grundzeug.container.plugins.ContainerBeanListResolutionPlugin` handles situations where you want to
register multiple implementations with the same contract and retrieve all of them at once during bean resolution. This
plugin is also registered in containers by default, so you don't have to do anything extra to use it, just register
multiple beans under a ``BeanList[...]`` contract:

.. code-block:: python

        class IBean:
            ...

        class Bean1(IBean):
            ...

        class Bean2(IBean):
            ...

        container = Container()
        container.register_factory[BeanList[IBean]](lambda: Bean1())
        container.register_factory[BeanList[IBean]](lambda: Bean2())
        beans = container.resolve[BeanList[IBean]]()
        assert isinstance(beans, BeanList)
        assert len(beans) == 2
        assert all(isinstance(b, IBean) for b in beans)


ContainerConverterResolutionPlugin
==================================

The :py:class:`~grundzeug.container.plugins.ContainerConverterResolutionPlugin` is a plugin that handles functions
to convert objects from one type from another. It attempts to resolve the most specific converter according to
Liskov substitution:

.. code-block:: python

    container = Container()
    container.add_plugin(ContainerConverterResolutionPlugin())

    def _assert_false(x):
        assert False

    container.register_instance[Converter[Any, Any]](_assert_false)
    container.register_instance[Converter[Any, int]](_assert_false)
    container.register_instance[Converter[str, object]](Converter[str, object].identity())
    container.register_instance[Converter[str, int]](lambda x: int(x))

    # Should resolve the last converter, since it's the most specific:
    str_to_int = container.resolve[Converter[str, int]]()
    assert str_to_int("3") == 3

    # Should resolve the second last converter, since it's the most specific:
    str_to_obj = container.resolve[Converter[str, object]]()
    assert str_to_obj("3") == "3"

Configuration
=============

Grundzeug's configuration capabilities are implemented as a DI container plugin.

.. warning::

    TODO: Add a link to the documentation once the documentation is ready.

*************************************
Writing a container resolution plugin
*************************************

A container resolution plugin has 3 groups of members: one with members pertaining to registration, one pertaining to
resolution, and one related to registration listing.

In this tutorial, we'll rebuild the :py:class:`~grundzeug.container.plugins.ContainerSingleValueResolutionPlugin`:

.. code-block:: python

    class ContainerSingleValueResolutionPlugin(ContainerResolutionPlugin):

Registration
============

The first step is to implement the method that will be called when a bean is being registered:

.. code-block:: python

        def register(
                self,
                key: RegistrationKey,
                registration: ContainerRegistration,
                container: IContainer
        ) -> bool:
            registry = container.get_plugin_storage(self)

            if key in registry:
                raise ContainerAlreadyHasRegistrationError()
            registry[key] = registration
            return True

The registration key is a pair consisting of the contract and the bean's name (or ``None`` if the bean is not named).

The registration is a class that handles the lifetimes of the bean instances. This is precisely what the plugin should
return during resolution.

If this plugin does not support the contract specified in the key, this method should return ``False`` as soon as
possible.

Inside the implementation, we retrieve a dictionary that will be used as storage for the container we're registering
the bean in. A naive approach would be to store the registrations in a dictionary with containers as keys, but this
would lead to memory leaks. This is precisely why the :py:meth:`~grundzeug.container.impl.Container.get_plugin_storage`
is needed --- it provides a storage mechanism that will not cause challenging situations for the garbage collector.

On successful registration, the plugin should return ``True``.

Resolution
==========

Grundzeug containers resolve beans by starting at the container on which
:py:meth:`~grundzeug.container.interface.IContainer.resolve_bean` was called and ascending up the container tree until
one of the container plugins returns a :py:class:`~grundzeug.container.interface.ReturnMessage`.

At the beginning of the bean resolution procedure, the Grundzeug container calls
:py:meth:`~grundzeug.container.interface.ContainerResolutionPlugin.resolve_bean_create_initial_state` on each plugin,
which allows the plugins to initialize the initial (seed) state for the bean resolution.

.. code-block:: python

        def resolve_bean_create_initial_state(
                self,
                key: RegistrationKey,
                container: IContainer
        ) -> Any:
            return None

The state created by
:py:meth:`~grundzeug.container.interface.ContainerResolutionPlugin.resolve_bean_create_initial_state` will be the
initial state passed into the reducer that will be called for each container in the chain of containers:

.. code-block:: python

        def resolve_bean_reduce(
                self,
                key: RegistrationKey,
                local_state: Any,
                container: IContainer,
                ancestor_container: IContainer
        ) -> Union[ReturnMessage, ContinueMessage, NotFoundMessage]:
            registry = ancestor_container.get_plugin_storage(self)

            if key in registry:
                registration = registry[key]
                return ReturnMessage(RegistrationBeanResolver(registration=registration, container=container))
            return NotFoundMessage(None)


.. code-block:: python

        def resolve_bean_postprocess(
                self,
                key: RegistrationKey,
                local_state: Any,
                container: IContainer
        ) -> Any:
            return NotFoundMessage(None)

Registration listing
====================

.. code-block:: python

        def registrations(
                self,
                container: IContainer
        ) -> typing.Iterable[typing.Tuple[RegistrationKey, ContainerRegistration]]:
            registry = container.get_plugin_storage(self)
            return registry.items()
