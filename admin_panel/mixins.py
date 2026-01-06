from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from accounts.models import User


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False

        return (
                user.is_superuser or
                getattr(user, "role", None) == User.ROLE_ADMIN or
                getattr(user, "role", None) == User.ROLE_WATCHER_ADMIN
        )
