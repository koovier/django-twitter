from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):
    """
    this function checks whether the request user is the owner of the comment
    - if @action detail=False, only has_permission will be checked.
    - if @action detail=True, both has_permission and has_object_permission will be checked.
    Error message contains IsObjectOwner.message
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user
    