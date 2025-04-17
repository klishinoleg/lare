class ServiceException(Exception):
    ...


class RepositoryException(ServiceException):
    ...


class RepositoryIsNotSet(RepositoryException):
    ...
