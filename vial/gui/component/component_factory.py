class ComponentRegistry:
    _registry = {}
    ct = {}

    @classmethod
    def register_component_tool(cls, func):
        cls.ct[func.__name__] = func
        return func

    @classmethod
    def register(cls, object_id):
        """
        Decorator to register a custom creator method for an object ID.
        :param object_id: Unique ID for the object type
        """
        def decorator(factory_method):
            cls._registry[object_id] = factory_method
            return factory_method

        return decorator

    @classmethod
    def create(cls, object_id, callback) -> "GuiComponent":
        """
        Create an object using the custom factory method associated with the given ID.
        :param object_id: Unique ID for the object type
        :param callback: A Callback object to pass to the creator method
        :param args: Additional arguments for the creator method
        :param kwargs: Additional keyword arguments for the creator method
        :return: The created object
        """
        if object_id not in cls._registry:
            raise ValueError(f"Unknown component with id: {object_id}")
        return cls._registry[object_id](callback)