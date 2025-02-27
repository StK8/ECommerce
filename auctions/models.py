from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# 'User' table
class User(AbstractUser):
    watchlist = models.ManyToManyField('Listing', null=True, blank=True, related_name="watching_users")


# 'Comments' table
class Comment(models.Model):
    text = models.CharField(max_length=1000)
    datetime = models.DateTimeField(auto_now=True)
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="comments")
    listing = models.ForeignKey("Listing", on_delete=models.CASCADE, related_name="comment")

    def __str__(self):
        return f"{self.datetime}: {self.text}"


# 'Bids' table
class Bid(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="bids")
    listing = models.ForeignKey("Listing", on_delete=models.CASCADE, related_name="bids")

    def __str__(self):
        return f"${self.amount} bid on {self.listing_id} by {self.user_id}"


# 'Categories' table
class Category(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.name}"


# 'Listings' table
class Listing(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=400)
    url = models.URLField(null=True, blank=True)
    categories = models.ManyToManyField(Category, null=True, blank=True)
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="created_listings")
    init_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.1)])
    current_price = models.DecimalField(max_digits=10, decimal_places=2,
                                        validators=[MinValueValidator(0.1)], default=0.1)
    #bid = models.ForeignKey("Bids", on_delete=models.PROTECT, null=True, blank=True)
    is_active = models.IntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(1)])
    winner = models.ForeignKey("User", on_delete=models.CASCADE, related_name="won_listings",
                               default=None, null=True, blank=True)

    def __str__(self):
        return f"Listing: {self.name}, desc: {self.description}"


