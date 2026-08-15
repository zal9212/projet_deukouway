from rest_framework import permissions

class IsClient(permissions.BasePermission):
    """Permission accordée uniquement aux utilisateurs identifiés comme clients / locataires."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'is_client', False))


class IsOwner(permissions.BasePermission):
    """Permission accordée uniquement aux utilisateurs ayant le rôle propriétaire."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'is_owner', False))


class IsVerifiedOwner(permissions.BasePermission):
    """Permission accordée aux propriétaires dont le KYC a été validé par un SuperAdmin.

    Distinct de `is_active` (qui gère uniquement la capacité de connexion) :
    un propriétaire non vérifié peut s'authentifier mais ne peut pas publier
    de logement tant que son dossier n'est pas approuvé.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'is_owner', False) and
            getattr(request.user, 'is_verified', False)
        )


class IsSuperAdmin(permissions.BasePermission):
    """Permission accordée exclusivement aux administrateurs de la plateforme."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (getattr(request.user, 'is_superadmin', False) or request.user.is_superuser or request.user.is_staff)
        )


class AdminOrReadOnly(permissions.BasePermission):
    """Lecture publique ou authentifiée pour tous, écriture restreinte aux SuperAdmins."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (getattr(request.user, 'is_superadmin', False) or request.user.is_superuser or request.user.is_staff)
        )


class IsPropertyOwner(permissions.BasePermission):
    """Permission au niveau de l'objet : vérifie que l'utilisateur est le propriétaire du logement."""
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if getattr(request.user, 'is_superadmin', False) or request.user.is_superuser:
            return True
        owner_id = getattr(obj, 'owner_id', None) or getattr(getattr(obj, 'owner', None), 'id', None)
        return owner_id == request.user.id


class IsReservationOwner(permissions.BasePermission):
    """Permission au niveau de l'objet : vérifie que l'utilisateur est le client ou le propriétaire associé à la réservation."""
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if getattr(request.user, 'is_superadmin', False) or request.user.is_superuser:
            return True
        client_id = getattr(obj, 'client_id', None) or getattr(getattr(obj, 'client', None), 'id', None)
        
        # Prop de la réservation ou demande de réservation
        prop = getattr(obj, 'property', None)
        owner_id = getattr(prop, 'owner_id', None) if prop else None
        if not owner_id and prop and hasattr(prop, 'owner'):
            owner_id = getattr(prop.owner, 'id', None)
            
        return request.user.id in (client_id, owner_id)
