from django.contrib import admin
from .models import Item, Wallet, PayoutTransaction

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'type_badge', 'category', 'city', 'user', 'is_approved', 'status', 'created_at')
    list_filter = ('is_approved', 'type', 'category', 'status', 'created_at', 'city')
    search_fields = ('title', 'description', 'city', 'user__username', 'user__email')
    list_editable = ('status', 'is_approved')
    
    fieldsets = (
        ('Basic information', {
            'fields': ('user', 'title', 'description', 'category', 'finder')
        }),
        ('Type and Status', {
            'fields': ('type', 'status', 'is_approved', 'is_priority')
        }),
        ('Media and Location', {
            'fields': ('image', 'city')
        }),
        ('Reward', {
            'fields': ('reward_amount',)
        }),
        ('Service information', {
            'fields': ('created_at','latitude', 'longitude', 'is_reward_paid', 'embedding'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at',)

    actions = ['make_reunited', 'approve_items', 'reject_items']

    @admin.action(description='Mark selected items as reunited')
    def make_reunited(self, request, queryset):
        updated = queryset.update(status='reunited')

        self.message_user(request, f'Successfully updated posts: {updated}. Related chats will be closed.')
    
    @admin.action(description='Approve selected listings')
    def approve_items(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, "The selected listings have been successfully approved.")

    @admin.action(description='Remove from publication (reject)')
    def reject_items(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, "The selected listings have been removed from publication.")

    def type_badge(self, obj):
        return obj.get_type_display()
    type_badge.short_description = 'Type'


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    list_filter = ('balance',)
    search_fields = ('user__username', 'user__email')

@admin.register(PayoutTransaction)
class PayoutTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email')
    list_editable = ('status',)
