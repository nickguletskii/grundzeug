Container plugins
=================

Base interface
--------------

Grundzeug containers can be extended by implementing ContainerResolutionPlugins, which allow you to implement custom
registration and resolution logic:

ContainerResolutionPlugin
"""""""""""""""""""""""""

.. autoclass:: grundzeug.container.interface.ContainerResolutionPlugin
   :members:
   :undoc-members:
   :inherited-members:

Available plugins
-----------------

ContainerAmbiguousResolutionPluginBase
""""""""""""""""""""""""""""""""""""""

.. autoclass:: grundzeug.container.plugins.ContainerAmbiguousResolutionPluginBase
   :members:
   :undoc-members:
   :inherited-members:

ContainerBeanListResolutionPlugin
"""""""""""""""""""""""""""""""""

.. autoclass:: grundzeug.container.plugins.ContainerBeanListResolutionPlugin
   :members:
   :undoc-members:
   :inherited-members:

ContainerConfigurationResolutionPlugin
""""""""""""""""""""""""""""""""""""""

.. autoclass:: grundzeug.container.plugins.ContainerConfigurationResolutionPlugin
   :members:
   :undoc-members:
   :inherited-members:

ContainerConverterResolutionPlugin
""""""""""""""""""""""""""""""""""

.. autoclass:: grundzeug.container.plugins.ContainerConverterResolutionPlugin
   :members:
   :undoc-members:
   :inherited-members:

ContainerSingleValueResolutionPlugin
""""""""""""""""""""""""""""""""""""

.. autoclass:: grundzeug.container.plugins.ContainerSingleValueResolutionPlugin
   :members:
   :undoc-members:
   :inherited-members:


Plugin interface
----------------

ReturnMessage
"""""""""""""

The following classes are used by the containers to communicate with plugins:

.. autoclass:: grundzeug.container.ReturnMessage
   :members:
   :undoc-members:
   :inherited-members:

ContinueMessage
"""""""""""""""

.. autoclass:: grundzeug.container.ContinueMessage
   :members:
   :undoc-members:
   :inherited-members:

NotFoundMessage
"""""""""""""""

.. autoclass:: grundzeug.container.NotFoundMessage
   :members:
   :undoc-members:
   :inherited-members:

Type conversion
---------------

register_contract_to_type_converter
"""""""""""""""""""""""""""""""""""

.. autofunction:: grundzeug.container.contracts.register_contract_to_type_converter

convert_contract_to_type
""""""""""""""""""""""""

.. autofunction:: grundzeug.container.contracts.convert_contract_to_type

Utilities
---------

lookup_container_plugin_by_type
"""""""""""""""""""""""""""""""

.. autofunction:: grundzeug.container.utils.lookup_container_plugin_by_type