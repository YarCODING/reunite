from django.urls import path
from .views import items
from .views import rewards

urlpatterns = [
    path("", items.index, name="home"),
    path("ping/", items.ping, name="ping"),
    path("items/<int:item_id>/", items.item_detail, name="item-detail"),
    path("items/", items.item_list, name="items"),
    path("items/map/", items.all_items_map_view, name="map"),
    path('dashboard/', items.dashboard, name='dashboard'),
    path('dashboard/list/', items.dashboard_list, name='dashboard_list'),
    path('dashboard/add/', items.dashboard_add, name='dashboard_add'),
    path('dashboard/item/<int:item_id>/edit/', items.edit_item, name='edit_item'),
    path('item/<int:item_id>/found-self/', items.cancel_search_self_view, name='cancel-search-self'),
    path('dashboard/item/<int:item_id>/delete/', items.delete_item, name='delete_item'),
    path('item/<int:item_id>/add-reward/', rewards.create_reward_payment_session, name='create-reward-session'),
    path('chat/confirm-reunite/<str:chatroom_name>/', rewards.confirm_reunite_view, name='confirm-reunite'),
    path('wallet/', rewards.request_withdrawal_view, name='wallet-page'),
    path('wallet/request-withdrawal/', rewards.request_withdrawal_view, name='request-withdrawal')
]