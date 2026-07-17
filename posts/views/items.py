from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.db.models import Count, Avg
from django.http import HttpResponse
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from ..models import Item, Wallet
from ..forms import ItemForm
from ..utils import check_matches_and_notify
import decimal

def index(request):
    desc = _("Reunite is a modern, community-driven platform designed to reconnect lost belongings with their rightful owners. Safe, secure, and fast.")
    featured_items = Item.objects.filter(is_approved=True).filter(status='active').order_by('-is_priority', '-created_at')[:3]
    return render(request, 'posts/index.html', {'items': featured_items, 'desc':desc})



def item_list(request):
    items = Item.objects.filter(is_approved=True).filter(status='active').order_by('-is_priority', '-created_at')

    selected_categories = request.GET.getlist('category', '')
    selected_type = request.GET.get('type', '')
    selected_city = request.GET.get('city', '')
    search_query = request.GET.get('q', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if selected_categories:
        items = items.filter(category__in=selected_categories)

    if selected_type:
        items = items.filter(type=selected_type)

    if selected_city:
        items = items.filter(city__icontains=selected_city)

    if search_query:
        items = items.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    if date_from:
        items = items.filter(created_at__date__gte=date_from)

    if date_to:
        items = items.filter(created_at__date__lte=date_to)

    return render(request, 'posts/item_list.html', {
        'items': items,
        'item_categories': Item.CATEGORY_CHOICES,
        'item_types': Item.TYPE_CHOICES,

        'selected_categories': selected_categories,
        'selected_type': selected_type,
        'selected_city': selected_city,
        
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
    })



def all_items_map_view(request):
    cities_data = (
        Item.objects.filter(status="active")
        .values("city")
        .annotate(
            count=Count("id"),
            lat=Avg("latitude"),
            lng=Avg("longitude")
        )
    )
    
    cities_list = []
    for item in cities_data:
        cities_list.append({
            'city': item['city'],
            'count': item['count'],
            'lat': float(item['lat']) if item['lat'] is not None else 0.0,
            'lng': float(item['lng']) if item['lng'] is not None else 0.0,
        })
    
    return render(request, "posts/map.html", {
        "cities_json": cities_list  
    })



def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if not item.is_approved and request.user != item.user:
        return redirect('items')
    return render(request, 'posts/item_detail.html', {'item': item})



@login_required
def dashboard(request):
    items = Item.objects.filter(user=request.user).order_by('status', '-created_at')
    return render(request, 'posts/dashboard.html', {'items': items})



@login_required
@require_GET
def dashboard_list(request):
    items = Item.objects.filter(user=request.user).order_by('status', '-created_at')
    return render(request, 'posts/partials/dashboard_items.html', {'items': items})




@login_required
@require_http_methods(["GET", "POST"])
def dashboard_add(request):
    FREE_POST_LIMIT = 2
    
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        
        if not request.user.has_premium:
            current_date = now()
            monthly_posts_count = Item.objects.filter(
                user=request.user,
                created_at__month=current_date.month,
                created_at__year=current_date.year
            ).count()
            
            if monthly_posts_count >= FREE_POST_LIMIT:
                error_msg = f"You have reached your limit of {FREE_POST_LIMIT} free posts this month. Upgrade to Reunite Hope for unlimited listings!"
                return render(request, 'posts/partials/dashboard_form.html', {
                    'form': form, 
                    'limit_error': error_msg
                })

        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            
            if request.user.has_premium:
                item.is_approved = True
                item.is_priority = True
            else:
                item.is_approved = False
            
            item.save()

            # AI
            check_matches_and_notify(item)

            items = Item.objects.filter(user=request.user).order_by('-created_at')
            
            response = render(request, 'posts/partials/dashboard_items.html', {'items': items})
            response['HX-Trigger'] = 'itemCreated'
            return response
    else:
        form = ItemForm()
        
    return render(request, 'posts/partials/dashboard_form.html', {'form': form})



@login_required
@require_http_methods(["POST"])
def cancel_search_self_view(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)
    
    if item.status == 'reunited':
        return redirect('item-detail', item_id=item.id)

    item.status = 'reunited'
    
    if item.is_reward_paid and item.reward_amount > 0:
        owner_wallet, _ = Wallet.objects.get_or_create(user=request.user)

        refund_amount = decimal.Decimal(str(item.reward_amount))
        
        owner_wallet.balance += refund_amount
        owner_wallet.save()
        
        item.reward_amount = 0.00
        item.is_reward_paid = False
        item.save()
        
        messages.success(request, f"Listing closed! Out of €{refund_amount} reward, 100% has been returned to your Wallet.")
    else:
        item.save()
        messages.success(request, "Listing successfully closed. Glad you found your item!")

    return redirect('dashboard')



@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)
    
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ItemForm(instance=item)
        
    return render(request, 'posts/edit_item.html', {'form': form, 'item': item})



@login_required
@require_POST
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)
    item.delete()
    
    if request.headers.get('HX-Request'):
        return HttpResponse("")
        
    return redirect('dashboard')





def ping(request):
    return HttpResponse("pong", content_type="text/plain")