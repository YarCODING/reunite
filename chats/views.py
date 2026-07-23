from django.shortcuts import render, get_object_or_404, redirect
from allauth.account.decorators import verified_email_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404
from posts.models import Item
from django.db.models import Max
from .models import*
from .forms import*

@login_required
def chat_list_view(request):
    chatrooms = request.user.chat_groups.filter(is_private=True).annotate(
        latest_message=Max('chat_messages__created') 
    ).order_by(
        'is_closed',
        '-latest_message'
    )

    return render(request, 'chats/chats_list.html', {'chatrooms': chatrooms})

@login_required
@verified_email_required
def chat_view(request, chatroom_name='public-chat'):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    
    if getattr(chat_group, 'is_closed', False) and not request.user.has_premium:
        if request.htmx:
            return render(request, 'chats/partials/premium_lock_partial.html')
        return render(request, 'chats/premium_lock.html', {'chat_group': chat_group})

    if request.user.has_premium:
        chat_messages = chat_group.chat_messages.all()
    else:
        chat_messages = chat_group.chat_messages.all()[:30]

    form = ChatmessageCreateForm()

    other_user = None
    if chat_group.is_private:
        if request.user not in chat_group.members.all():
            raise Http404()
        for member in chat_group.members.all():
            if member != request.user:
                other_user = member
                break

    if getattr(chat_group, 'is_closed', False) and request.method == "POST":
        raise Http404("Archived chats are read-only.")

    if request.htmx:
        form = ChatmessageCreateForm(request.POST)
        if form.is_valid(): 
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()
            context = {
                'message' : message,
                'user' : request.user
            }
            return render(request, 'chats/partials/chat_message_p.html', context)
        
    context = {
        'chat_messages' : chat_messages, 
        'form' : form,
        'other_user' : other_user,
        'chatroom_name': chatroom_name,
        'chat_group': chat_group,
    }

    return render(request, 'chats/chat.html', context)


@login_required
@verified_email_required
def get_or_create_chatroom(request, username, item_id=None):
    if request.user.username == username:
        return redirect('home')
    
    other_user = get_object_or_404(User, username=username)
    
    item = None
    if item_id:
        item = get_object_or_404(Item, id=item_id)
    
    chatroom = ChatGroup.objects.filter(
        is_private=True,
        item=item,
        members=request.user
    ).filter(members=other_user).first()
    
    if not chatroom:
        chatroom = ChatGroup.objects.create(is_private=True, item=item)
        chatroom.members.add(request.user, other_user)
        
    return redirect('chatroom', chatroom.group_name)