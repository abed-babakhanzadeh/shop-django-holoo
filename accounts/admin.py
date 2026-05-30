from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from jalali_date.admin import ModelAdminJalaliMixin
import jdatetime

from .models import CustomUser, Address, BankAccount, OTPCode, Wallet

admin.site.unregister(Group)

admin.site.site_header = "پنل مدیریت فروشگاه یکپارچه با هلو"
admin.site.site_title = "مدیریت فروشگاه"
admin.site.index_title = "پیشخوان مدیریت"

# --- Inlines (نمایش جداول مرتبط درون صفحه کاربر) ---
class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    classes = ('collapse',)

class BankAccountInline(admin.TabularInline):
    model = BankAccount
    extra = 0
    classes = ('collapse',)
    
# کلاس اینلاین برای کیف پول
class WalletInline(admin.StackedInline):
    model = Wallet
    can_delete = False
    verbose_name_plural = 'کیف پول کاربر'

# --- Main User Admin ---
@admin.register(CustomUser)
class CustomUserAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'mobile', 
        'get_full_name_or_company', 
        'customer_type', 
        'status', 
        'registered_via',
        'is_mobile_verified',
        'get_jalali_date_joined'
    )
    
    list_filter = ('status', 'customer_type', 'registered_via', 'is_mobile_verified')
    search_fields = ('mobile', 'national_id', 'economic_code', 'holoo_erp_code', 'first_name', 'last_name', 'company_name')
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')
    
    inlines = [WalletInline, AddressInline, BankAccountInline] # اضافه شدن آدرس و حساب بانکی به انتهای فرم کاربر

    fieldsets = (
        (_('اطلاعات ورود'), {
            'fields': ('mobile', 'password')
        }),
        (_('وضعیت و تاییدات'), {
            'fields': ('status', 'customer_type', 'is_mobile_verified', 'is_blacklisted', 'is_active', 'registered_via')
        }),
        (_('اطلاعات هویتی و شرکتی'), {
            'fields': ('first_name', 'last_name', 'company_name', 'national_id', 'economic_code', 'telephone')
        }),
        (_('اعتبار مالی هلو'), {
            'fields': ('credit_limit',),
        }),
        (_('ارتباط با حسابداری هلو'), {
            'fields': ('holoo_customer_code', 'holoo_erp_code'),
            'classes': ('collapse',) 
        }),
        (_('دسترسی‌های سیستمی'), {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('تاریخ‌ها'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('نام / شرکت'))
    def get_full_name_or_company(self, obj):
        full_name = obj.get_full_name()
        if obj.company_name:
            return f"{obj.company_name} ({full_name})" if full_name else obj.company_name
        return full_name or "---"

    @admin.display(description=_('تاریخ عضویت'), ordering='date_joined')
    def get_jalali_date_joined(self, obj):
        if obj.date_joined:
            return jdatetime.datetime.fromgregorian(datetime=obj.date_joined).strftime('%Y/%m/%d %H:%M')
        return "---"

    actions = ['approve_users', 'suspend_users']

    @admin.action(description=_('تایید نهایی کاربران انتخاب شده'))
    def approve_users(self, request, queryset):
        updated = queryset.update(status='approved', is_active=True)
        self.message_user(request, f'{updated} کاربر تایید شدند.')

    @admin.action(description=_('معلق کردن کاربران'))
    def suspend_users(self, request, queryset):
        updated = queryset.update(status='suspended', is_active=False)
        self.message_user(request, f'{updated} کاربر معلق شدند.')


@admin.register(OTPCode)
class OTPCodeAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('mobile', 'code', 'is_used', 'get_jalali_created_at', 'is_valid')
    list_filter = ('is_used',)
    search_fields = ('mobile',)
    readonly_fields = ('mobile', 'code', 'created_at', 'expires_at', 'is_used')

    @admin.display(description=_('تاریخ ایجاد'), ordering='created_at')
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime('%Y/%m/%d %H:%M:%S')
        return "---"