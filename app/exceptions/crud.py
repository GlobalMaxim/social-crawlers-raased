class CRUDException(Exception):
    """
    CRUD operation failed
    """

class PostHasNoSocialRequest(Exception):
    """
    Post has no social request
    """

class NoSuchProfileRequest(Exception):
    """
    Profile requests with such id does not exist
    """

class DuplicateEntry(Exception):
    """
    Duplicate entry during create CRUD operation
    """

