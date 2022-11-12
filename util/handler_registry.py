# Provide a registry for managing different implementations
# Version: 1.0.1
# Changelog:
# 1.0.1: Fixed _registered_handlers field is shared among different HandlerRegistry
from typing import *

__all__ = ['HandlerRegistry', 'register_handler']
_TK = TypeVar('_TK')
_TV = TypeVar('_TV')


class HandlerRegistry(Generic[_TK, _TV]):
    """A registry for handling multiple implementations via keys. See ``avenger.config`` for example."""
    _registered_handlers = {}  # type: Dict[_TK, Type[_TV]]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registered_handlers = {}

    @classmethod
    def register_handler(cls, handler_name: _TK, handler_class: Type[_TV]) -> None:
        """Register a handler to current registry. If ``handler_name`` already registered before, then the previous
        registered handler will be replaced by new handler class.
        """
        cls._registered_handlers[handler_name] = handler_class

    @classmethod
    def get_handler(cls, handler_name: _TK) -> Optional[Type[_TV]]:
        """Get registered handler with name ``handler_name``. Return None if not found."""
        return cls._registered_handlers.get(handler_name, None)

    @classmethod
    def unregister_handler(cls, handler_name: _TK) -> None:
        """Unregister (remove registered) handler with name ``handler_name``."""
        del cls._registered_handlers[handler_name]

    @classmethod
    def get_all_handler_names(cls) -> List[_TK]:
        """Get all registered handler names."""
        return list(cls._registered_handlers.keys())


def register_handler(registry: Type[HandlerRegistry[_TK, _TV]], handler_name: Union[_TK, Sequence[_TK]]) \
        -> Callable[[_TV], _TV]:
    """A decorator for registering handler.

    Example::

    >>> class MyHandler:
    ...     @staticmethod
    ...     def do_some_job():
    ...         raise NotImplementedError
    >>> class MyRegistry(HandlerRegistry[str, MyHandler]):
    ...     pass
    >>> @register_handler(MyRegistry, 'impl1')
    ... class MyHandlerImpl1:
    ...     @staticmethod
    ...     def do_some_job():  # this is inherited from MyHandler
    ...         print('do jobs MyHandlerImpl1')
    >>> @register_handler(MyRegistry, 'impl2')
    ... class MyHandlerImpl2:
    ...     @staticmethod
    ...     def do_some_job():  # this is inherited from MyHandler
    ...         print('do jobs MyHandlerImpl2')

    Then the implementation class can be accessed via different ``handler_name`` by::

    >>> MyRegistry.get_handler('impl1').do_some_job()
    do jobs MyHandlerImpl1

    For multiple handler names, the decorator can be used multiple times or pass handler names as a sequence::
    >>> @register_handler(MyRegistry, ['impl1', 'impl2'])
    ... class MyHandlerImpl3:
    ...     @staticmethod
    ...     def do_some_job():  # this is inherited from MyHandler
    ...         print('do jobs MyHandlerImpl3')

    :param registry: The registry class to be registered.
    :param handler_name: The name for current handler.
    :return A decorator function for class.
    """
    def do_handler_registration(handler_class: Type[_TV]):
        if isinstance(handler_name, (list, tuple)):
            for name in handler_name:
                registry.register_handler(name, handler_class)
        else:
            registry.register_handler(handler_name, handler_class)
        return handler_class
    return do_handler_registration
