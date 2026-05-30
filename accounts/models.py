from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

# ==========================================
# 1. Choices & Constants
# ==========================================
class CustomerType(models.TextChoices):
    UNKNOWN = 'unknown', _('نامشخص / در انتظار تعیین')
    RETAIL = 'retail', _('مشتری عادی')        # نگاشت به SellPrice در هلو
    WHOLESALE = 'wholesale', _('بنک‌دار')    # نگاشت به SellPrice2 در هلو
    CREDIT = 'credit', _('مشتری چکی')        # نگاشت به SellPrice3 در هلو
    VIP = 'vip', _('مشتری VIP')             # نگاشت به SellPrice4 در هلو

class UserStatus(models.TextChoices):
    PENDING = 'pending', _('در انتظار بررسی ادمین')
    APPROVED = 'approved', _('تایید شده')
    REJECTED = 'rejected', _('رد شده')
    SUSPENDED = 'suspended', _('معلق')

class RegistrationMethod(models.TextChoices):
    OTP = 'otp', _('پیامک (OTP)')
    PASSWORD = 'password', _('رمز عبور')
    ADMIN = 'admin', _('توسط ادمین')
    HOLOO = 'holoo', _('ایمپورت از هلو')


# ==========================================
# 2. User Manager
# ==========================================
class CustomUserManager(BaseUserManager):
    def create_user(self, mobile, password=None, **extra_fields):
        if not mobile:
            raise ValueError(_('شماره موبایل باید وارد شود.'))
        user = self.model(mobile=mobile, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('status', UserStatus.APPROVED)
        extra_fields.setdefault('customer_type', CustomerType.VIP)
        extra_fields.setdefault('is_mobile_verified', True)
        extra_fields.setdefault('registered_via', RegistrationMethod.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(mobile, password, **extra_fields)


# ==========================================
# 3. Core User Model
# ==========================================
class CustomUser(AbstractUser):
    username = None 
    
    # --- احراز هویت و امنیت ---
    mobile = models.CharField(max_length=15, unique=True, verbose_name=_('شماره موبایل'))
    is_mobile_verified = models.BooleanField(default=False, verbose_name=_('موبایل تایید شده'))
    registered_via = models.CharField(
        max_length=20, 
        choices=RegistrationMethod.choices, 
        default=RegistrationMethod.OTP, 
        verbose_name=_('روش ثبت‌نام')
    )

    # --- وضعیت و نوع در سیستم ---
    customer_type = models.CharField(
        max_length=20, 
        choices=CustomerType.choices, 
        default=CustomerType.UNKNOWN, 
        verbose_name=_('نوع مشتری (تجاری)')
    )
    status = models.CharField(
        max_length=20, 
        choices=UserStatus.choices, 
        default=UserStatus.PENDING, 
        verbose_name=_('وضعیت حساب')
    )
    is_blacklisted = models.BooleanField(default=False, verbose_name=_('لیست سیاه هلو')) # <-- جدید

    # --- اطلاعات هویتی و شرکتی ---
    national_id = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('کد ملی / شناسه ملی'))
    economic_code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('کد اقتصادی'))
    company_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('نام شرکت/فروشگاه'))
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('تلفن ثابت'))

    # --- اعتبارسنجی و مالی هلو ---
    credit_limit = models.DecimalField(
        max_digits=15, 
        decimal_places=0, 
        default=0, 
        blank=True, 
        verbose_name=_('سقف اعتبار چکی (تومان)')
    ) # <-- جدید

    # --- ارتباط با حسابداری هلو ---
    holoo_erp_code = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        unique=True,
        verbose_name=_('شناسه هلو (ErpCode)')
    )
    holoo_customer_code = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        unique=True,
        verbose_name=_('کد طرف حساب هلو (Code)'),
        help_text=_('کد عددی مشتری در هلو (ReturnParam1)')
    ) # <-- جدید
    
    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = [] 

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('کاربر')
        verbose_name_plural = _('کاربران')

    def __str__(self):
        return f"{self.company_name or self.first_name or self.mobile} ({self.mobile})"

    # متد داینامیک برای فهمیدن اینکه این کاربر کدام ستون قیمت هلو را باید ببیند
    @property
    def holoo_price_field(self):
        price_map = {
            CustomerType.RETAIL: 'sellprice',      # قیمت فروش ۱
            CustomerType.WHOLESALE: 'sellprice2',  # قیمت فروش ۲
            CustomerType.CREDIT: 'sellprice3',     # قیمت فروش ۳
            CustomerType.VIP: 'sellprice4',        # قیمت فروش ۴
            CustomerType.UNKNOWN: 'sellprice',     # پیش‌فرض برای نامشخص‌ها
        }
        return price_map.get(self.customer_type, 'sellprice')


# ==========================================
# 4. Address Model
# ==========================================
class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses', verbose_name=_('کاربر'))
    title = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('عنوان آدرس'))
    
    province = models.CharField(max_length=100, verbose_name=_('استان'))
    city = models.CharField(max_length=100, verbose_name=_('شهر'))
    postal_code = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('کد پستی'))
    full_address = models.TextField(verbose_name=_('آدرس کامل'))
    
    recipient_name = models.CharField(max_length=150, blank=True, null=True, verbose_name=_('نام گیرنده'))
    recipient_mobile = models.CharField(max_length=15, blank=True, null=True, verbose_name=_('موبایل گیرنده'))
    
    is_default = models.BooleanField(default=False, verbose_name=_('آدرس پیش‌فرض'))

    class Meta:
        verbose_name = _('آدرس')
        verbose_name_plural = _('آدرس‌ها')

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# ==========================================
# 5. Bank Account Model
# ==========================================
class BankAccount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_accounts', verbose_name=_('کاربر'))
    
    bank_name = models.CharField(max_length=50, verbose_name=_('نام بانک'))
    owner_name = models.CharField(max_length=150, verbose_name=_('نام صاحب حساب'))
    card_number = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name=_('شماره کارت'))
    shaba_number = models.CharField(max_length=30, unique=True, blank=True, null=True, verbose_name=_('شماره شبا (IR)'))
    
    is_approved = models.BooleanField(default=False, verbose_name=_('تایید شده توسط ادمین'))
    is_default = models.BooleanField(default=False, verbose_name=_('حساب پیش‌فرض'))

    class Meta:
        verbose_name = _('حساب بانکی')
        verbose_name_plural = _('حساب‌های بانکی')

    def save(self, *args, **kwargs):
        if self.is_default:
            BankAccount.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# ==========================================
# 6. Wallet Model
# ==========================================
class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet', verbose_name=_('کاربر'))
    balance = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('موجودی (تومان)'))

    class Meta:
        verbose_name = _('کیف پول')
        verbose_name_plural = _('کیف‌های پول')

    def __str__(self):
        return f"کیف پول {self.user.mobile} - موجودی: {self.balance}"


# ==========================================
# 7. OTP Code Model
# ==========================================
class OTPCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='otp_codes',
        verbose_name=_('کاربر')
    )
    mobile = models.CharField(max_length=15, verbose_name=_('شماره موبایل'))
    code = models.CharField(max_length=6, verbose_name=_('کد تایید'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('زمان ایجاد'))
    expires_at = models.DateTimeField(verbose_name=_('زمان انقضا'))
    is_used = models.BooleanField(default=False, verbose_name=_('استفاده شده'))

    class Meta:
        verbose_name = _('کد یکبار مصرف')
        verbose_name_plural = _('کدهای یکبار مصرف')

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at