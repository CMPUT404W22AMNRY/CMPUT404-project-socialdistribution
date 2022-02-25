from django.contrib import admin
from .models import FriendList, FriendRequest

# Register your models here.
class FriendListAdmin(admin.ModelAdmin):
    list_filter = ['author']
    list_display = ['author']
    search_feilds = ['author']
    readonly_feilds = ['author']

    class Meta:
        model = FriendList

class FriendRequestAdmin(admin.ModelAdmin):
    list_filter = ['sender', 'reciever']
    list_display = ['sender', 'reciever']
    search_feild = ['sender', 'reciever']

    class Meta:
        model = FriendRequest

admin.site.register(FriendList, FriendListAdmin)
admin.site.register(FriendRequest, FriendRequestAdmin)