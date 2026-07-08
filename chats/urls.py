from django.urls import path
from .views import *

urlpatterns = [
    path("list", chat_list_view, name="chat-list"),
    path("", chat_view, name="chat"),
    path("chat/<str:username>", get_or_create_chatroom, name="start-chat"),
    path("chat/<str:username>/<int:item_id>", get_or_create_chatroom, name="start-chat-with-item"),
    path("room/<chatroom_name>", chat_view, name="chatroom"),
]