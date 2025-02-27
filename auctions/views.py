from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django import forms
from .models import User, Category, Comment, Listing, Bid


class NewListingForm(forms.Form):
    name = forms.CharField(label="Title:", max_length=64, widget=forms.TextInput)
    description = forms.CharField(label="Description:", max_length=400, widget=forms.Textarea)
    init_price = forms.DecimalField(label="Starting price:", min_value=0.1, widget=forms.NumberInput)
    url = forms.URLField(label="Image:", required=False, widget=forms.TextInput)
    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all(), label="Categories:",
                                                widget=forms.CheckboxSelectMultiple)


class BidForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.listing_id = kwargs.pop('listing_id')
        self.listing = Listing.objects.get(pk=self.listing_id)
        super(BidForm, self).__init__(*args, **kwargs)

    bid_value = forms.DecimalField(label="", widget=forms.NumberInput(attrs={'placeholder': 'Bid value'}))

    def clean_bid_value(self):
        cleaned_data = self.cleaned_data['bid_value']
        if cleaned_data > self.listing.current_price:
            return cleaned_data
        else:
            raise forms.ValidationError("Your bid cannot be lower than the current price.")


class CommentForm(forms.Form):
    text = forms.CharField(label="", max_length=400,
                           widget=forms.TextInput(attrs={'placeholder': 'Comment'}))

def index(request):
    active_listings = Listing.objects.filter(is_active=1)
    return render(request, "auctions/index.html", {
        "active_listings": active_listings
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def new_listing(request):
    if request.method == "POST":
        form = NewListingForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            description = form.cleaned_data["description"]
            init_price = form.cleaned_data["init_price"]
            url = form.cleaned_data["url"]
            categories = form.cleaned_data["categories"]
            user_id = request.user.id
            user = User.objects.get(pk=user_id)
            listing = Listing(
                name=name, description=description, init_price=init_price, user=user, url=url)
            listing.save()
            #setting current_price equal to init_price
            listing.current_price = init_price
            for category in categories:
                listing.categories.add(category)
            listing.save()
            return redirect("index")
        else:
            return render(request, "auctions/new_listing", {
                "form": form
            })

    else:
        return render(request, "auctions/new_listing.html", {
            "form": NewListingForm()
        })


def listing(request, listing_id):
    if Listing.objects.get(pk=listing_id) == None:
        return redirect("index")
    else:
        listing = Listing.objects.get(pk=listing_id)
        comments_count = listing.comment.all().count()
        if comments_count == 0:
            comments = "No comments were left here."
        else:
            comments = listing.comment.all()
        image_url = None
        if listing.url:
            image_url = listing.url
        is_active = True
        is_winner = False
        if listing.is_active == 0:
            is_active = False
        in_watchlist = False
        is_author = False

        if request.user.is_authenticated:
            user_id = request.user.id
            current_user = User.objects.get(pk=user_id)
            # checking if current user has current listing in watchlist
            try:
                current_user.watchlist.get(pk=listing_id)
                in_watchlist = True
            except Listing.DoesNotExist:
                in_watchlist = False;
            # checking if current user is the author of the listing
            if current_user == listing.user:
                is_author = True
            # checking if current user won the listing
            if current_user == listing.winner:
                is_winner = True
        return render(request, "auctions/listing.html", {
            "listing": listing,
            "listing_id": listing_id,
            "in_watchlist": in_watchlist,
            "is_author": is_author,
            "is_active": is_active,
            "is_winner": is_winner,
            "comments": comments,
            "comments_count": comments_count,
            "bid_form": BidForm(listing_id=listing_id),
            "comment_form": CommentForm(),
            "image_url": image_url
        })


@login_required()
def watchlist_add(request, listing_id):
    if request.method == "POST":
        if Listing.objects.get(pk=listing_id) == None:
            return redirect("index")
        else:
            user_id = request.user.id
            current_user = User.objects.get(pk=user_id)
            listing = Listing.objects.get(pk=listing_id)
            current_user.watchlist.add(listing)
            current_user.save()
            return redirect("listing", listing_id)
    else:
        pass


@login_required()
def watchlist_delete(request, listing_id):
    if request.method == "POST":
        if Listing.objects.get(pk=listing_id) == None:
            return redirect("index")
        else:
            user_id = request.user.id
            current_user = User.objects.get(pk=user_id)
            listing = Listing.objects.get(pk=listing_id)
            current_user.watchlist.remove(listing)
            current_user.save()
            # redirect to the referring URL
            return redirect(request.META.get('HTTP_REFERER'))
    else:
        pass


@login_required()
def place_bid(request, listing_id):
    if request.method == "POST":
        if Listing.objects.get(pk=listing_id) == None:
            return redirect("index")
        else:
            listing = Listing.objects.get(pk=listing_id)
            if listing.is_active == 0:
                return redirect("index")
            bid_form = BidForm(request.POST, listing_id=listing_id)
            user_id = request.user.id
            current_user = User.objects.get(pk=user_id)
            in_watchlist = False
            try:
                current_user.watchlist.get(pk=listing_id)
                in_watchlist = True
            except Listing.DoesNotExist:
                pass
            if bid_form.is_valid():
                bid_value = bid_form.cleaned_data["bid_value"]
                listing.current_price = bid_value
                listing.save()
                bid = Bid(amount=bid_value, user=current_user, listing=listing)
                bid.save()
                return redirect("listing", listing_id)
            else:
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "listing_id": listing_id,
                    "in_watchlist": in_watchlist,
                    "bid_form": bid_form,
                    "is_active": True,
                    "image_url": listing.url
                })
    else:
        return redirect("listing", listing_id=listing_id)


@login_required()
def listing_close(request, listing_id):
    if request.method == "POST":
        if Listing.objects.get(pk=listing_id) == None:
            return redirect("index")
        else:
            listing = Listing.objects.get(pk=listing_id)
            if listing.is_active == 1:
                #closing the listing
                listing.is_active = 0
                #find user who placed the max bid and make them winner
                bids = Bid.objects.filter(listing_id=listing_id)
                #if there's at least one bid then assign the winner, else there's no winner
                if bids.count() > 0:
                    listing.winner = bids.order_by('-amount').first().user
                else:
                    listing.winner = None
                listing.save()
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "listing_id": listing_id,
                    "is_active": False,
                    "is_winner": False
                })
    else:
        pass


@login_required()
def add_comment(request, listing_id):
    if request.method == "POST":
        #if listing not exists
        if Listing.objects.get(pk=listing_id) == None:
            return redirect("index")
        else:
            listing = Listing.objects.get(pk=listing_id)
            #if listing is closed
            if listing.is_active == 0:
                return redirect("index")
            #if listing exists and active
            else:
                form = CommentForm(request.POST)
                if form.is_valid():
                    comment_text = form.cleaned_data["text"]
                    user_id = request.user.id
                    current_user = User.objects.get(pk=user_id)
                    comment = Comment(text=comment_text, user=current_user, listing=listing)
                    comment.save()
                    return redirect("listing", listing_id)
                else:
                    return redirect("index")


@login_required()
def watchlist(request):
    user_id = request.user.id
    current_user = User.objects.get(pk=user_id)
    watchlist = current_user.watchlist.all()
    return render(request, "auctions/watchlist.html", {
        "watchlist": watchlist
    })


def categories_list(request):
    categories = Category.objects.all()
    listings_in_category_count = {}
    for category in categories:
        # active listings in each category
        active_listings = Listing.objects.filter(categories=category, is_active=1)
        listings_in_category_count[category] = active_listings.count()
    return render(request, "auctions/categories_list.html", {
        "categories_count": listings_in_category_count
    })


def category(request, category_id):
    category = Category.objects.get(pk=category_id)
    active_listings = category.listing_set.filter(is_active=1)
    return render(request, "auctions/category.html", {
        "active_listings": active_listings,
        "category": category
    })


def listings_sell(request):
    user_id = request.user.id
    current_user = User.objects.get(pk=user_id)
    listings_sell = Listing.objects.filter(user=current_user)
    return render(request, "auctions/listings_sell.html", {
        "listings_sell": listings_sell
    })


def listings_won(request):
    user_id = request.user.id
    current_user = User.objects.get(pk=user_id)
    listings_won = Listing.objects.filter(winner=current_user)
    return render(request, "auctions/listings_won.html", {
        "listings_won": listings_won
    })