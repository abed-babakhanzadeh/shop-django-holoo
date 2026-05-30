from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

# ==========================================
# 1. Product Category (دسته‌بندی‌ها)
# ==========================================
class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name=_('نام دسته‌بندی'))
    slug = models.SlugField(max_length=200, unique=True, allow_unicode=True, verbose_name=_('آدرس (Slug)'))
    
    # ساختار درختی سایت (Parent-Child)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name=_('دسته والد'))
    
    # ارتباط با ساختار دو سطحی هلو
    is_holoo_main_group = models.BooleanField(default=False, verbose_name=_('آیا گروه اصلی هلو است؟'))
    holoo_erp_code = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name=_('شناسه هلو (ErpCode)'))
    
    # ظاهر سایت
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name=_('تصویر دسته/بنر'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    sort_order = models.IntegerField(default=0, verbose_name=_('ترتیب نمایش'))

    class Meta:
        verbose_name = _('دسته‌بندی')
        verbose_name_plural = _('دسته‌بندی‌ها')
        ordering = ['sort_order', 'name']

    def __str__(self):
        # رفع باگ: جلوگیری از حلقه بی‌نهایت در دسته‌بندی‌های درختی اشتباه
        full_path = [self.name]
        k = self.parent
        depth = 0
        while k is not None and depth < 10:
            full_path.append(k.name)
            k = k.parent
            depth += 1
        return ' / '.join(full_path[::-1])

# ==========================================
# 2. Brand Model (برندها)
# ==========================================
class Brand(models.Model):
    name = models.CharField(max_length=200, verbose_name=_('نام برند'))
    slug = models.SlugField(max_length=200, unique=True, allow_unicode=True, verbose_name=_('آدرس (Slug)'))
    logo = models.ImageField(upload_to='brands/', blank=True, null=True, verbose_name=_('لوگو'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))

    class Meta:
        verbose_name = _('برند')
        verbose_name_plural = _('برندها')
        ordering = ['name']

    def __str__(self):
        return self.name

# ==========================================
# 3. Product Model (کالا)
# ==========================================
class Product(models.Model):
    # --- اطلاعات پایه سایت ---
    name = models.CharField(max_length=255, verbose_name=_('نام کالا'))
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True, verbose_name=_('آدرس (Slug)'))
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name=_('دسته‌بندی فرعی'))
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name=_('برند'))
    
    description = models.TextField(blank=True, verbose_name=_('توضیحات معرفی محصول'))
    short_description = models.CharField(max_length=500, blank=True, verbose_name=_('توضیح کوتاه / خلاصه'))
    
    # --- اطلاعات یکتای هلو ---
    holoo_code = models.CharField(max_length=50, blank=True, null=True, db_index=True, verbose_name=_('کد کالا هلو (Code)'))
    holoo_erp_code = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name=_('شناسه هلو (ErpCode)'))
    unit_name = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('واحد اندازه‌گیری (مثلا: عدد)'))
    unit_erp_code = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('شناسه واحد هلو'))

    # --- موجودی و انبار ---
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('موجودی کل (Few)'))
    stock_carton = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('موجودی کارتن (FewKarton)'))
    count_in_carton = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name=_('تعداد در کارتن'))
    count_in_basteh = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name=_('تعداد در بسته')) # <-- اضافه شد
    
    is_active = models.BooleanField(default=True, verbose_name=_('نمایش در سایت'))
    
    # --- ساختار قیمت‌گذاری هلو (10 سطح قیمت فروش) ---
    buy_price = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('قیمت خرید (مبنای سود)'))
    
    sellprice = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('قیمت فروش 1 (عادی)'))
    sellprice2 = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('قیمت فروش 2 (بنک‌دار)'))
    sellprice3 = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('قیمت فروش 3 (چکی)'))
    sellprice4 = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('قیمت فروش 4 (VIP)'))
    sellprice5 = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('قیمت فروش 5'))
    sellprice6 = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('قیمت فروش 6'))
    sellprice7 = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('قیمت فروش 7'))
    sellprice8 = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('قیمت فروش 8'))
    sellprice9 = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('قیمت فروش 9'))
    sellprice10 = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('قیمت فروش 10'))
    
    sellprice_karton = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('قیمت فروش کارتن')) # <-- اضافه شد

    # --- تاریخ‌ها و همگام‌سازی ---
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد در سایت'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('آخرین تغییر در سایت'))
    last_holoo_sync = models.DateTimeField(null=True, blank=True, verbose_name=_('آخرین همگام‌سازی با هلو')) # <-- اضافه شد

    class Meta:
        verbose_name = _('محصول')
        verbose_name_plural = _('محصولات')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - ({self.holoo_code or 'بدون کد'})"

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    def get_price_for_user(self, user):
        """
        محاسبه قیمت کالا بر اساس نقش کاربر (استفاده در Viewها و سیستم محاسبات مالی)
        """
        if user and user.is_authenticated:
            price_field = user.holoo_price_field
            return getattr(self, price_field, self.sellprice)
        return self.sellprice


# ==========================================
# 4. Product Images (گالری تصاویر)
# ==========================================
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name=_('محصول'))
    image = models.ImageField(upload_to='products/%Y/%m/', verbose_name=_('تصویر'))
    is_main = models.BooleanField(default=False, verbose_name=_('تصویر اصلی'))
    alt_text = models.CharField(max_length=200, blank=True, verbose_name=_('متن جایگزین (سئو)'))

    class Meta:
        verbose_name = _('تصویر محصول')
        verbose_name_plural = _('گالری تصاویر محصولات')
        ordering = ['-is_main', 'id']


# ==========================================
# 5. Wishlist (علاقه‌مندی‌ها)
# ==========================================
class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist', verbose_name=_('کاربر'))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_('محصول'))
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('علاقه‌مندی')
        verbose_name_plural = _('لیست علاقه‌مندی‌ها')
        unique_together = ('user', 'product')


# ==========================================
# 6. Stock Notification (سیستم خبرم کن - جدید)
# ==========================================
class StockNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stock_notifications', verbose_name=_('کاربر'))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_notifications', verbose_name=_('محصول'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ درخواست'))
    is_notified = models.BooleanField(default=False, verbose_name=_('اطلاع‌رسانی شده؟'))

    class Meta:
        verbose_name = _('اطلاع‌رسانی موجودی')
        verbose_name_plural = _('درخواست‌های اطلاع‌رسانی موجودی')
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.mobile} - {self.product.name}"