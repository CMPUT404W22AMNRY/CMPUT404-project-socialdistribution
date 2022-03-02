from django.db import models
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from follow.signals import (
    request_create,
    request_reject,
    request_cancel,
    request_accept,
)


class AlreadyExistsError(IntegrityError):
    pass


class FollowManager(models.Manager):
    def followings(self, user):
        qs = Follow.objects.filter(follower=user).all()
        followings = [_.followee for _ in qs]
        return followings

    def followers(self, user):
        qs = Follow.objects.filter(followings=user).all()
        followers = [_.follower for _ in qs]
        return followers

    def true_friend(self, user):
        qs1 = Follow.objects.filter(follower=user, true_friend=True).all()
        qs2 = Follow.objects.filter(followee=user, true_friend=True).all()
        friend1 = [_.followee for _ in qs1]
        friend2 = [_.follower for _ in qs2]

        return list(set(friend1 + friend2))

    def request(self, user):
        qs = (Request.objects.select_related("from_user", "to_user").filter(to_user=user).all())
        requests = list(qs)
        return requests

    def sent_request(self, user):
        qs = (Request.objects.select_related("from_user", "to_user").filter(from_user=user).all())
        requests = list(qs)
        return requests

    def follow_request(self, from_user, to_user):
        '''create follow request'''
        if from_user == to_user:
            raise ValidationError("User cannot follow themselves.")

        if self.check_follow(from_user, to_user):
            raise AlreadyExistsError("Users has already followed.")

        if Request.objects.filter(from_user = from_user,
                                to_user = to_user).exists():
            raise AlreadyExistsError("User has sent the follow request.")

        request, created = Request.objects.get_or_create(from_user=from_user, to_user=to_user)
        if created is False:
            raise AlreadyExistsError("User has sent the follow request.")

        request_create.send(sender=request)
        return request

    def unfollow(self, follower, followee):
        try:
            relation = Follow.objects.get(follower=follower, followee=followee)
            try:
                true_friend_bidirect = Follow.objects.get(follower=followee, followee=follower)
                if relation.true_friend and true_friend_bidirect.true_friend:
                    true_friend_bidirect.true_friend = True
                    true_friend_bidirect.save()
            except Follow.DoesNotExist:
                pass
            relation.delete()
            return True
        except Follow.DoesNotExist:
            return False

    def check_follow(self, follower, followee):
        try:
            relation = Follow.objects.get(follower=follower, followee=followee)
            return True
        except Follow.DoesNotExist:
            return False

    def check_true_friend(self, follower, followee):
        if Follow.objects.filter(
            follower=follower,
            followee=followee,
            true_friend=True).exists() and Follow.objects.filter(
                follower=followee,
                followee=follower,
                true_friend=True).exists():
            return True
        else:
            return False


class Follow(models.Model):
    followee = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="followee")
    follower = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="follower")
    created = models.DateTimeField(default=timezone.now)
    true_friend = models.BooleanField(default=False)
    objects = FollowManager()

    class Meta:
        unique_together = ("followee", "follower")

    def __str__(self):
        return f"{self.followee.Username} is followed by {self.follower.Username}"

    def save(self, *args, **kwargs):
        if self.followee == self.follower:
            raise ValidationError("User cannot follow themselves.")
        super().save(*args, **kwargs)


class Request(models.Model):
    from_user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="from_user")
    to_user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="to_user")
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("from_user", "to_user")

    def __str__(self):
        return f"{self.from_user.Username}'s request to follow {self.to_user.Username}"

    def accept(self):
        relation, created = Follow.objects.get_or_create(follower=self.from_user, followee=self.to_user)

        if created is False:
            raise AlreadyExistsError(f"{self.from_user.Username} has already followed {self.to_user.Username}")
        
        request_accept.send(sender=self, from_user=self.from_user, to_user=self.to_user)

        try:
            relation_reverse = Follow.objects.get(follower=self.to_user, followee=self.from_user)
            relation_reverse.real_friend = True
            relation_reverse.save()
            relation.real_friend = True
            relation.save()
        except Follow.DoesNotExist:
            pass

        self.delete()
        return True

    def reject(self):
        self.delete()
        request_reject.send(sender=self)
        return True

    def cancel(self):
        request_cancel.send(sender=self)
        self.delete()
        return True
