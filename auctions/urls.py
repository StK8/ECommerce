from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("new_listing", views.new_listing, name="new_listing"),
    path("listings/<str:listing_id>/add", views.watchlist_add, name="watchlist_add"),
    path("listings/<str:listing_id>/delete", views.watchlist_delete, name="watchlist_delete"),
    path("listings/<str:listing_id>/close", views.listing_close, name="listing_close"),
    path("listings/<str:listing_id>/bid", views.place_bid, name="place_bid"),
    path("listings/<str:listing_id>/comment", views.add_comment, name="add_comment"),
    path("listings/<str:listing_id>", views.listing, name="listing"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("categories/<str:category_id>", views.category, name="category"),
    path("categories", views.categories_list, name="categories_list"),
    path("listings_sell", views.listings_sell, name="listings_sell"),
    path("listings_won", views.listings_won, name="listings_won")
]
