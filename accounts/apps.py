from django.apps import AppConfig
from django.conf import settings

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        # settings.py에서 제어 가능
        # from django.contrib.auth.models import User
        
        if getattr(settings, "USE_KOREAN_NAME_FORMAT", True):
            self.setup_korean_name_format()

    def setup_korean_name_format(self):
        from django.contrib.auth.models import User
        # 원본 저장
        User._original_get_full_name = User.get_full_name
        User._original_get_short_name = User.get_short_name

        def korean_get_full_name(self):
            if self.first_name and self.last_name:
                return f"{self.last_name}{self.first_name}".strip()
            elif self.last_name:
                return self.last_name
            elif self.first_name:
                return self.first_name
            return self.username

        def korean_get_short_name(self):
            # 성만 변환 (한국식)
            return self.last_name or self.first_name or self.username

        User.get_full_name = korean_get_full_name
        User.get_short_name = korean_get_short_name
