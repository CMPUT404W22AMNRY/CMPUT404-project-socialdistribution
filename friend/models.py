from pyexpat import model
from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone

class FriendList(models.Model):
    author = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="author")
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="friends")

    def __str__(self):
        return self.author.username()

    def addFriend(self, account):
        addee_friendList = FriendList.objects.get(author=account)
        if account in self.friends.all()and self.author in addee_friendList.friends.all():
            self.friends.add(account)
            addee_friendList.friends.add(self.author)
            self.save()
        else: raise("An error occur")

    def delFriend(self, account):
        removee_friendList = FriendList.objects.get(author=account)
        if account in self.friends.all() and self.author in removee_friendList.friends.all():
            self.friends.remove(account)
            removee_friendList.friends.remove(self.author)
            self.save()
        else: raise("Not friend yet")
    
    def checkFriend(self, account):
        if account in self.friends.all():
            return True
        return False 

class FriendRequest(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(settings.AUTH_USER.MODEL, on_delete=models.CASCADE, related_name="receiver")
    is_active = models.BooleanField(blank=True, null=False, default=True)
    time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sender.username()

    def accept(self):
        sender_friend_list = FriendList.objects.get(author=self.sender)
        receiver_friend_list = FriendList.objects.get(author=self.receiver)
        if receiver_friend_list and sender_friend_list:
            receiver_friend_list.addFriend(self.sender)
            sender_friend_list.addFriend(self.receiver)
            self.is_active = False
            self.save()
        else: raise("An error occurs")
    
    def decline(self):
        self.is_active = False
        self.save()

    def cancel(self):
        self.is_active = False
        self.save()