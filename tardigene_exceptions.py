"""
Contains custom exceptions for the Tardigene classes and functions 
"""

class TardigeneException(Exception):
    """
    Base exception
    """
    pass

class EmptyDatabaseError(TardigeneException):
    """
    Raised if user is trying to use bioinformatics analysis tools against empty database
    """
    pass 

class FileNotSeenError(TardigeneException):
    pass

class InvalidFormatError(TardigeneException):
    pass

class MissingDependancyError(TardigeneException):
    pass
