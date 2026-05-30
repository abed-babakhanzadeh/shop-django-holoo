from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    # این خط نام اپلیکیشن را در کل پنل ادمین تغییر می‌دهد
    verbose_name = _('مدیریت حساب‌های کاربری')