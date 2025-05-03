class ServiceException(Exception):
    ...


class RepositoryException(ServiceException):
    ...


class RepositoryIsNotSet(RepositoryException):
    ...


class EventBrokerException(ServiceException):
    ...


class EventBrokerNoHandlerException(EventBrokerException):
    ...
